#!/usr/bin/env python3

import decode_apk as dec
import extract_features_from_xml as extr
import nlp_analysis as nlp
import os
import subprocess
import sys
import fire
import yaml
from termcolor import colored

#set constants
strings_xml_path = "./data/output/res/values/strings.xml"

#create temporary data folder
def setup():
    if not os.path.exists("data"):
        os.makedirs("data")

#remove data folder and all contents
def cleanup():
    """Clears the data directory"""
    subprocess.call(["rm", "-rf", "data"])

#Helper function to "pretty" print accessibility service descriptions
def print_descriptions(original_descriptions, en_descriptions):
    print("\n-------------------- DESCRIPTIONS: --------------------\n")
    for d in original_descriptions:
        print(d)
        print("\n-------------------------------------------------------\n")

    print("\n------------------- EN Descriptions: ------------------\n")
    for d in en_descriptions:
        print(d)
        print("\n-------------------------------------------------------\n")

def sanitize_desc(descriptions):
    res = []
    for desc in descriptions:
        desc = desc.replace('-', '')
        desc = desc.replace('*', '')
        desc = desc.replace('•', '')
        res.append(desc)
    return res

def get_action_phrases(accessibility_config_file_list, desc):
    action_phrases = []  

    #extract description strings
    original_descriptions = extr.extract_accessibility_service_descriptions(strings_xml_path, accessibility_config_file_list)

    if original_descriptions is not None:
        #translate descriptions to english and sanitize
        en_descriptions = sanitize_desc(nlp.translate_descriptions(original_descriptions))
        
        #extract action phrases using nlp
        for description in en_descriptions:
            desc_ap = nlp.extract_action_phrases(description)
            if(desc_ap):
                action_phrases = action_phrases + desc_ap

        #print descriptions if specified by user
        if desc:
            print_descriptions(original_descriptions, en_descriptions)
            #print(action_phrases)
    else:
        return None
    
    return action_phrases

def decode_apk(apk_path):
    """This command only decodes a specified apk using apktool, without performing any further analysis"""
    setup()
    out = dec.decode(apk_path)
    print(out)

def analyze_apk(apk_path, print_desc:bool=False, print_events:bool=False):
    """Performs analysis of the specified file as long as it is compatible with apktool input formats"""
    setup()

    #Decode apk with apktool
    decoded_apk_path = dec.decode(apk_path)
    category = 'uncategorized'

    #Extract list of accessibility config files
    print('[' + colored('*', 'green') + ']', 'Extracting accessibility config files from manifest...')
    try:
        accessibility_config_file_list = extr.get_accessibility_config_files(decoded_apk_path)
    except extr.NoManifestError:
        print(colored('[*] No manifest was found for this apk...\n[*] Cleaning up...', 'red'))
        cleanup()
        print(colored('[*] Aborting analysis...', 'red'))
        return 1

    if(accessibility_config_file_list is None):
        print(colored('[*] Failed to extract accessibility config files...\n[*] Cleaning up...', 'red'))
        cleanup()
        print(colored('[*] Aborting analysis...', 'red'))
        return 1

    if(print_events):
        print('[' + colored('*', 'green') + ']', ' Extracting accessibility event types the app listens for...')
        #Get dictionary of Event Types the app listens for
        event_type_dict = extr.extract_accessibility_events(accessibility_config_file_list)
        if(event_type_dict is None):
            print(colored("[*] Failed to extract AccessibilityEvent types from accessibility config files... \n[*] Resuming analysis...", 'red'))
            
        #Placeholder. Results will be used in 2nd Phase to guide dynamic analysis
        print('-------------------- Event Types: --------------------')
        print(yaml.dump(event_type_dict, sort_keys=False, default_flow_style=False))
        print('------------------------------------------------------')
    
    #Extract Accessibility Service descriptions and action phrases
    print('[' + colored('*', 'green') + ']', 'Analyzing accessibility service descriptions...')
    if not os.path.isfile(strings_xml_path):
        print(colored('[*] Failed to locate strings.xml. No further analysis possible...\n[*] Cleaning up...', 'red'))
        cleanup()
        print(colored('[*] Aborting analysis...', 'red'))
        return 1
    else:
        action_phrases = get_action_phrases(accessibility_config_file_list, print_desc)
        if(action_phrases is None):
            print(colored('[*] Failed to extract accessibility service description...\n[*] Cleaning up...', 'red'))
            cleanup()
            return 2
        
        category, stemmed_action_phrases = nlp.get_functionality_category(action_phrases)

        if(category != 'uncategorized'):
            print(colored('[*] App provides sufficiently meaningful description of its accessibility services and was placed in the following category: ' + category, 'green'))
        else:
            print(colored('[*] The analyzed app doesn\'t provide a meaningful accessibility service description, which is an indicator for misuse of accessibility APIs and even malicious behavior...', 'yellow'))

    print('[' + colored('*', 'green') + ']','APK analysis done!')

    cleanup()

#Similar to analyze_apk. Analyzes all .apk files in a given directory.
def analyze_directory(dir_path, print_desc:bool = False, print_events:bool = False):
    """This command allows for analysis of all .apk files in a specified directory."""

    for filename in os.listdir(dir_path):
        
        #For now only supports .apk files
        if not filename.endswith(".apk"):
            continue

        else:
            apk_path = os.path.join(dir_path, filename)     #Set full apk path to currently analyzed .apk file
            analyze_apk(apk_path, print_desc, print_events)
            inp = input('Abort analysis? [Y/n]\n')
            if(inp == 'Y'):
                print('[', colored('*', 'yellow'), ']',  'Cleaning up...')
                cleanup()
                exit(0)

    print('[' + colored('*', 'green') + ']','Directory analysis done!')

    #clean directory
    cleanup()

#Pipeline class to easily add functionality to Fire CLI
class Pipeline(object):
    """PHA Scanner for Android Malware leveraging Accessibility Services"""
    def __init__(self):
        self.apk = analyze_apk
        self.dir = analyze_directory
        self.d = decode_apk
        self.c = cleanup


if __name__ == "__main__":
     fire.Fire(Pipeline)