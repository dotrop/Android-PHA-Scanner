#!/usr/bin/env python3

from googletrans import Translator
import spacy
from spacy import displacy

def translate_descriptions(desc_list):
    translator = Translator()
    translation = []
    for desc in desc_list:
        translation.append(translator.translate(desc, dest='en'))

    english_descriptions = [t.text for t in translation]
    return english_descriptions

def extract_action_phrases(description):
    nlp = spacy.load("en_core_web_sm")

    doc = nlp(description)
    action_phrases = []

    ignore_tokens = set()

    for token in doc:
        #print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.shape_, token.is_alpha, token.is_stop)

        #check if token is negated, thus to be ignored
        if(token in ignore_tokens):
            continue

        #check if current token is a verb
        if(token.pos_ == 'VERB'):

            #check for negation, if verb is negated, ignore it and add all other verbs in sentence that depend on negated verb to ignore_tokens
            if(check_for_negation(token)):
                for child in token.children:
                    if(child.pos_ == 'VERB' and child.dep_ == 'xcomp'):
                        ignore_tokens.add(child)
                continue

            action_phrases += get_verb_action_phrases(token)
        
    #print(action_phrases)
    return action_phrases

def check_for_negation(node):
    for child in node.children:
        if(child.dep_ == 'neg'):
            return True
    return False

def get_verb_action_phrases(verb):
    action_phrases = []

    #Initialize queue and set of visited nodes for BFS
    visited = set()
    queue = []
    queue.append(verb)
    visited.add(verb)

    new_clause_dep = ['conj', 'xcomp']
    
    #Perform BFS
    while queue:
        node = queue.pop(0)

        if(node.dep_ == 'csubj'):
            continue
        
        #objects after next VERB node will not have a relationship to current verb
        if(node.pos_ == 'VERB' and not(verb == node) and (node.dep_ in new_clause_dep)):
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
        #update visited and queue
        for child in node.children:
            if child not in visited:
                visited.add(child)
                queue.append(child)

    return action_phrases




""" extract_action_phrases('Turn it on will help Network Master stop apps and extend your battery life.' + 
        'Network Master uses accessibility service to optimize your device only.' +
        'We will never use it to collect your privacy information. If you receive warnings about privacy, please ignore.')
 """
extract_action_phrases("When TalkBack is on, it provides spoken feedback so that you can use your device without looking at the screen. This can be helpful for people who are blind or have low vision.\n\nTo navigate using TalkBack:\n• Swipe right or left to move between items\n• Double-tap to activate an item\n• Drag two fingers to scroll\n\nTo turn off TalkBack:\n• Tap the switch. You’ll see a green outline. Double-tap the switch.\n• On the confirmation message, tap OK. Then double-tap OK.")
