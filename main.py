#!/usr/bin/env python3

import decode_apk as dec
import extract_features_from_xml as extr
import nlp_analysis as nlp
import os
import subprocess
import sys
import fire

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

#TODO: Implement helper function for description and action phrase extraction
def get_action_phrases(accessibility_config_file_list, desc):
    action_phrases = []  

    #extract description strings
    original_descriptions = extr.extract_accessibility_service_descriptions(strings_xml_path, accessibility_config_file_list)

    if original_descriptions is not None:
        #translate descriptions to english
        en_descriptions = nlp.translate_descriptions(original_descriptions)
        
        #extract action phrases using nlp
        for description in en_descriptions:
            desc_ap = nlp.extract_action_phrases(description)
            if(desc_ap):
                action_phrases = action_phrases + desc_ap

        #print descriptions if specified by user
        if desc:
            print_descriptions(original_descriptions, en_descriptions)
            print(action_phrases)
    
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
    try:
        accessibility_config_file_list = extr.get_accessibility_config_files(decoded_apk_path)
    except extr.NoManifestError:
        print("No Manifest was found for this apk")
        cleanup()
        exit(1)

    if(accessibility_config_file_list is None):
        print("No accessibility config files found!")
        cleanup()
        exit(1)

    #Extract Accessibility Service descriptions and action phrases
    if not os.path.isfile(strings_xml_path):
        print("Failed to extract descriptions: No strings.xml found. Resuming analysis...")
    else:
        action_phrases = get_action_phrases(accessibility_config_file_list, print_desc)
        category, stemmed_action_phrases = nlp.get_functionality_category(action_phrases)
        
        print('App was categorized into category: ', category)


    #Get dictionary of Event Types the app listens for
    event_type_dict = extr.extract_accessibility_events(accessibility_config_file_list)
    if(event_type_dict is None):
        print("No AccessibilityEvent types could be extracted from accessibility config files")
        cleanup()
        exit(2)
    
    #Placeholder. Results will be used in 2nd Phase to guide dynamic analysis
    if(print_events):
        print(event_type_dict)
    print("Static analysis done!")

    cleanup()

#Similar to analyze_apk. Analyzes all .apk files in a given directory.
def analyze_directory(dir_path, print_desc:bool = False, print_events:bool = False):
    """This command allows for analysis of all .apk files in a specified directory."""
    
    setup()

    for filename in os.listdir(dir_path):
        
        #For now only supports .apk files
        if not filename.endswith(".apk"):
            continue

        else:
            apk_path = os.path.join(dir_path, filename)     #Set full apk path to currently analyzed .apk file
            decoded_apk_path = dec.decode(apk_path)         #Decode apk
            
            #extract config files if possible
            try:
                accessibility_config_file_list = extr.get_accessibility_config_files(decoded_apk_path)
            except extr.NoManifestError:
                print("No Manifest was found for this apk")
                continue
            
            #check if config files were found
            if accessibility_config_file_list is None:
                print("No accessibility config files found!")
                continue
            else:

                #Extract Accessibility Service descriptions and action phrases
                if not os.path.isfile(strings_xml_path):
                    print("Failed to extract descriptions. Resuming analysis...")
                else:
                    action_phrases = get_action_phrases(accessibility_config_file_list, print_desc)
                    category, stemmed_action_phrases = nlp.get_functionality_category(action_phrases)
                    print('App was categorized into category: ', category)

                #Extract Accessibility Event Types the app listens for
                event_type_dict = extr.extract_accessibility_events(accessibility_config_file_list)
                if event_type_dict is None:
                    print("No AccessibilityEvent types could be extracted from accessibility config files")
                    continue
                else:
                    if(print_events):
                        print(apk_path + " uses accessibility services and listens for the following events...")

                        #Placeholder. Results will be used in 2nd Phase to guide dynamic analysis
                        print(event_type_dict)

    print("Static analysis done!")

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