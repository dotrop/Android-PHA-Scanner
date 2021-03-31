#!/usr/bin/env python3

from googletrans import Translator
import spacy
from spacy import displacy
from nltk.stem.snowball import SnowballStemmer

# This function handles translation of a list of descriptions
# @return: list of english descriptions
def translate_descriptions(desc_list):
    translator = Translator()
    translation = []
    for desc in desc_list:
        translation.append(translator.translate(desc, dest='en'))

    english_descriptions = [t.text for t in translation]
    return english_descriptions

# This function extracts action phrases from a single description
# @return list of action phrases
def extract_action_phrases(description):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(description)

    new_clause_dep = ['conj', 'xcomp']
    action_phrases = []
    ignore_tokens = set()

    #displacy.serve(doc, style='dep')

    for token in doc:
        #check if token is negated, thus to be ignored
        if(token in ignore_tokens):
            continue

        #check if current token is a verb
        if(token.pos_ == 'VERB'):
            #check for negation, if verb is negated, ignore it and add all other verbs in sentence that depend on negated verb to ignore_tokens
            if(check_for_negation(token)):
                for child in token.children:
                    if(child.pos_ == 'VERB'):
                        ignore_tokens.add(child)
                continue

            action_phrases += get_verb_action_phrases(token, ignore_tokens)
    
    return action_phrases

# This function checks if a node is negated by one of its children
def check_for_negation(node):
    for child in node.children:
        if(child.dep_ == 'neg'):
            return True
    return False

# This function calculates the amount of matches between a list of stemmed action phrases and a set of matching rules
def get_matches(stemmed_action_phrases, rules):
    res = 0
    if not rules:
        return res
    for sap in stemmed_action_phrases:
        for rule in rules:
            if rule in sap:
                res += 1
    return res

# This function returns all the action phrases for a specific VERB node
# @return: all the action phrases for verb
def get_verb_action_phrases(verb, ignore_tokens):
    action_phrases = []

    #Initialize queue and set of visited nodes for BFS
    visited = set()
    queue = []
    queue.append(verb)
    visited.add(verb)

    # if a child VERB node has one of these dependency values, it should still be considered
    new_clause_dep = set(['conj', 'xcomp', 'advcl', 'ccomp', 'pcomp'])
    
    #Perform BFS
    done = False

    while queue and not done:
        node = queue.pop(0)

        if(node in ignore_tokens):
            continue

        if(node.dep_ == 'csubj'):
            continue
        
        #objects after next VERB node will not have a relationship to current verb
        if(node.pos_ == 'VERB' and verb != node and node.dep_ not in new_clause_dep):
            continue
        
        #check if node is a direct object
        if(node.dep_ == 'dobj'):

            #retrieve potential compound noun
            compound_found = False
            for pot_compound in node.children:
                if(pot_compound.dep_ == 'compound'):
                    action_phrases.append(verb.text + ' ' + (pot_compound.text + ' ' + node.text))
                    compound_found = True
                    break
            if not compound_found:
                action_phrases.append(verb.text + ' ' + node.text)
            done = True
        
        #check if child node is adverbial clause
        elif(node.dep_ == 'advcl' and node != verb):
            subj_found = False

            #Find passive subject
            for pot_subj in node.children:
                if(pot_subj.dep_ == 'nsubjpass'):
                    action_phrases.append(verb.text + ' ' + pot_subj.text + ' ' + node.text)
                    subj_found = True
                    break
            if not subj_found:
                action_phrases.append(verb.text + ' ' + node.text)
            done = True
        
        # check for prepositions
        elif(node.dep_ == 'prep'):
            for pot_obj in node.children:
                if('obj' in pot_obj.dep_):
                    action_phrases.append(verb.text + ' ' + node.text + ' ' + pot_obj.text)
            done = True

        # check for adverbial modifiers
        elif(node.dep_ == 'advmod'):
            action_phrases.append(verb.text + ' ' + node.text)
            done = True


        #update visited and queue
        for child in node.children:
            if child not in visited:
                visited.add(child)
                queue.append(child)

    return action_phrases

# This function takes a list of action phrases and returns their stemmed forms
def get_stemmed_action_phrases(action_phrases):
    stemmer = SnowballStemmer(language='english')
    res = []

    for ap in action_phrases:
        words = ap.split()
        stemmed_ap = ''
        for word in words:
            stemmed_ap += stemmer.stem(word) + ' '
        res.append(stemmed_ap.rstrip(' '))
    
    return res 


# This function checks if the given set of action phrases can be matches to any of the specified functionality categories
# @return: the inferred category aswell as the list of stemmed action phrases
def get_functionality_category(action_phrases):
    stemmed_action_phrases = get_stemmed_action_phrases(action_phrases)

    #Dictionary containing a matching pattern (list of stemmed action phrases) for each category of functionality
    category_rules = {
        "kill processes" : ['optim devic perform', 'stop app', 'drain app', 'stop function', 'extend batteri life', 'estimate batteri life', 'block app', 'boost phone', 'speed phone', 'save power', 'batteri', 'save effect', 'stop background applic', 'stop drain app', 'prevent app', 'boost devic', 'get % perform', 'stop killer', 'close app', 'clear cach', 'decreas power usag', 'decreas % usag'],
        "obtain notifications": ['catch event', 'obtain notif', 'detect notif', 'receiv respons', 'receiv app switch', 'give notif access'],
        "provide audio feedback": ['provid feedback', 'feedback', 'make sound', 'hear aloud', 'read aloud'],
        "capture audio": ['captur speech', 'process convers', 'voic command', 'intercept search'],
        "assist operating device": ['voic command', 'control android devic', 'control devic', 'control phon', 'navig screen', 'activ item', 'perform gestur','perform user action', 'emul user action', 'simul mous function', 'lock screen', 'brows screen', 'block oper', 'intercept search', 'hold smatphon', 'prevent oper', 'help someon', 'copi text content',  'disabl hardwar', 'block hardwar', 'prevent touch', 'prevent oper', 'enabl interfac', 'block touch', 'lock phone', 'take screenshot', 'use switch'],
        "read screen content": ['read text', 'read content', 'retriev window content', 'monitor screen app','scan screen', 'scan page', 'access page', 'copi website address', 'detect screen content', 'read screen content', 'retriev app content', 'select text', 'see text'],
        "modify screen content": ['fill', 'enter text', 'draw over screen', 'hide app', 'hide overlay app', 'enabl screen app', 'convert text', 'dictionari', 'translat page content', 'autofil', 'display notif', 'highlight', 'disabl default popup'],
        "auto perform actions": ['back', 'perform action', 'open power', 'open notif', 'perform system function', 'perform home', 'pull notif panel', 'start action', 'start task', 'turn screen', 'autom task', 'show set', 'open recent', 'launch side popup'],
        "detect foreground app": ['monitor amount', 'devic history', 'catch front', 'monitor app', 'monitor switch', 'monitor transit', 'find button'],
        "detect user actions" : ['observ action', 'receiv action', 'detect touch event', 'detect button press', 'press overlay button',  'log action', 'monitor action', 'saw ad', 'collect research inform', 'find button', 'listen volum'],
        "security": ['protect privaci', 'check links', 'protect you', 'lock apps', 'protect app', 'protect web brows', 'scan page', 'warn you'],
        "auto sign in": ['copi websit address', 'detail rememb', 'sign into app', 'transmit inform', 'autofil', 'fill usernam', 'retriev app content', 'fill login', 'login feature', 'detect you prompt']
    }

    res = 'uncategorized'       
    max = 0

    # Infer category by checking which one has the most matches
    for category, rules in category_rules.items():
        matches = get_matches(stemmed_action_phrases, rules)
        if(matches > max):
            res = category
            max = matches

    return res, stemmed_action_phrases
