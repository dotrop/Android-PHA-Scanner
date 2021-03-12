#!/usr/bin/env python3

import decode_apk as dec
import extract_accessibility_events as extr
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

def analyze_apk(apk_path, desc:bool = False):
    """Performs analysis of the specified file as long as it is compatible with apktool input formats"""
    setup()

    #Decode apk with apktool
    decoded_apk_path = dec.decode(apk_path)

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

    #print out accessibility service descriptions
    if os.path.isfile(strings_xml_path):
        extr.extract_accessibility_service_descriptions(strings_xml_path, accessibility_config_file_list, desc)
    else:
        print("Failed to extract descriptions. Resuming analysis...")


    #Get dictionary of Event Types the app listens for
    event_type_dict = extr.extract_accessibility_events(accessibility_config_file_list)
    if(event_type_dict is None):
        print("No AccessibilityEvent types could be extracted from accessibility config files")
        cleanup()
        exit(2)
        
    #Placeholder. Results will be used in 2nd Phase to guide dynamic analysis
    print(event_type_dict)
    print("Static analysis done!")

    cleanup(0)

def decode_apk(apk_path):
    """This command only decodes a specified apk using apktool, without performing any further analysis"""
    setup()
    out = dec.decode(apk_path)
    print(out)

#Similar to analyze_apk. Analyzes all .apk files in a given directory.
def analyze_directory(dir_path, desc:bool = False):
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
                #print out accessibility service descriptions
                #print out accessibility service descriptions
                if os.path.isfile(strings_xml_path):
                    extr.extract_accessibility_service_descriptions(strings_xml_path, accessibility_config_file_list, desc)
                else:
                    print("Failed to extract descriptions. Resuming analysis...")

                event_type_dict = extr.extract_accessibility_events(accessibility_config_file_list)
                if event_type_dict is None:
                    print("No AccessibilityEvent types could be extracted from accessibility config files")
                    continue
                else:
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