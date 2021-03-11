#!/usr/bin/env python3

import decode_apk as dec
import extract_accessibility_events as extr
import os
import subprocess
import sys
import fire

#create temporary data folder
def setup():
    if not os.path.exists("data"):
        os.makedirs("data")

#remove data folder and all contents
def cleanup(exitcode):
    subprocess.call(["rm", "-rf", "data"])
    exit(exitcode)

def analyze_apk(apk_path):
    print(apk_path)

    setup()

    #Decode apk with apktool
    decoded_apk_path = dec.decode(apk_path)

    #Extract list of accessibility config files
    try:
        accessibility_config_file_list = extr.get_accessibility_config_files(decoded_apk_path)
    except extr.NoManifestError:
        print("No Manifest was found for this apk")
        cleanup(1)

    if(accessibility_config_file_list is None):
        print("No accessibility config files found!")
        cleanup(1)

    #Get dictionary of Event Types the app listens for
    event_type_dict = extr.extract_accessibility_events(accessibility_config_file_list)
    if(event_type_dict is None):
        print("No AccessibilityEvent types could be extracted from accessibility config files")
        cleanup(2)
        

    print("Static analysis done!")
    print(event_type_dict)

    cleanup(0)

def analyze_directory(dir_path):
    print(dir_path)

class Pipeline(object):
    def __init__(self):
        self.apk = analyze_apk
        self.dir = analyze_directory

if __name__ == "__main__":
     fire.Fire(Pipeline)