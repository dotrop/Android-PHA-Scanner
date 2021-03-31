#!/usr/bin/env python3

import decode_apk as dec
import extract_features_from_xml as extr
import nlp_analysis as nlp
import os
import subprocess
import sys
import fire
import csv
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

#TODO: Implement helper function for description and action phrase extraction
def get_action_phrases(accessibility_config_file_list):
    action_phrases = []  

    #extract description strings
    original_descriptions = extr.extract_accessibility_service_descriptions(strings_xml_path, accessibility_config_file_list)

    if original_descriptions is not None:
        #translate descriptions to english and sanitize
        en_descriptions = nlp.translate_descriptions(original_descriptions)
        en_descriptions = sanitize_desc(en_descriptions)
        
        #extract action phrases using nlp
        for description in en_descriptions:
            desc_ap = nlp.extract_action_phrases(description)
            if(desc_ap):
                action_phrases = action_phrases + desc_ap
    else:
        print('No descriptions could be extracted...')
        return None, None, None

    return action_phrases,original_descriptions, en_descriptions

#Similar to analyze_apk. Analyzes all .apk files in a given directory.
def analyze_directory(dir_path):
    """This command allows for analysis of all .apk files in a specified directory."""
    
    setup()

    if not os.path.exists(os.path.join(dir_path, 'successful')):
        os.makedirs(os.path.join(dir_path, 'successful'))

    if not os.path.exists(os.path.join(dir_path, 'useless')):
        os.makedirs(os.path.join(dir_path, 'useless'))


    for filename in os.listdir(dir_path):
        
        #For now only supports .apk files
        if not filename.endswith(".apk"):
            continue

        else:
            apk_path = os.path.join(dir_path, filename)     #Set full apk path to currently analyzed .apk file
            decoded_apk_path = dec.decode(apk_path)         #Decode apk 

            try:
                name = extr.get_package_name(decoded_apk_path)
            except extr.NoManifestError:
                print("No Manifest was found for this apk. Moving to useless folder")
                os.rename(apk_path, os.path.join(dir_path, 'useless', filename))
                continue

            new_fn = name + '.apk'        
            
            #extract config files if possible
            try:
                accessibility_config_file_list = extr.get_accessibility_config_files(decoded_apk_path)
            except extr.NoManifestError:
                print("No Manifest was found for this apk. Moving to useless folder")
                os.rename(apk_path, os.path.join(dir_path, 'useless', new_fn))
                continue
            
            #check if config files were found
            if not accessibility_config_file_list:
                print("App doesnt use accessibility")
                os.rename(apk_path, os.path.join(dir_path, 'useless', new_fn))
                continue

            if accessibility_config_file_list is None:
                print('App uses accessibility but no config found')
                continue
            else:

                #Extract Accessibility Service descriptions and action phrases
                if not os.path.isfile(strings_xml_path):
                    print("Failed locate strings.xml. Resuming analysis...")
                    os.rename(apk_path, os.path.join(dir_path, 'useless', new_fn))
                    continue
                else:
                    with open('samples.csv', 'a') as csv_file:
                        writer = csv.writer(csv_file)
                        writer.writerow(name.split())

                    action_phrases, od, ed = get_action_phrases(accessibility_config_file_list)
                    if(od is None):
                        print("Failed to extract descriptions. Resuming analysis...")
                        #os.rename(apk_path, os.path.join(dir_path, 'useless', new_fn))
                        continue
                    category, stemmed_action_phrases = nlp.get_functionality_category(action_phrases)
                if(category == 'uncategorized'):
                    print_descriptions(od, ed)
                    print(action_phrases)
                    print(stemmed_action_phrases)
                    print(colored('Could not categorize app\'s functionality', 'yellow'))
                    print(name)
                    inp = input('Enter y to abort:\n')
                    if(inp == 'y'):
                        print('Aborting analysis...\nCleaning up...')
                        cleanup()
                        exit(0)
                    print('Resuming analysis...')
                    continue
                    
                else:
                    print_descriptions(od, ed)
                    print(stemmed_action_phrases)
                    print(colored(('App was categorized into category: ' + category),'green'))
                    print(name)
                    inp = input('Enter y to abort:\n')
                    if(inp == 'y'):
                        print('Aborting analysis...\nCleaning up...')
                        cleanup()
                        exit(0)
                    os.rename(apk_path, os.path.join(dir_path, 'successful', new_fn))
    subprocess.call(['sort', '-u', 'samples.csv', '-o', 'samples.csv'])
    print('Done!')

    #clean directory
    cleanup()

#Pipeline class to easily add functionality to Fire CLI
class Pipeline(object):
    """PHA Scanner for Android Malware leveraging Accessibility Services"""
    def __init__(self):
        self.run = analyze_directory
        self.c = cleanup


if __name__ == "__main__":
     fire.Fire(Pipeline)