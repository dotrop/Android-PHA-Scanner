#!/usr/bin/env python3

import subprocess
import os
from shutil import copy


output_dir = os.path.abspath(os.path.join('data', 'output'))

def decode(apk_path):
    
    #extract filename
    _ , filename = os.path.split(apk_path)

    #Create data directory if it doesn't exist
    if not os.path.exists("data"):
        os.makedirs("data")

    #Copy apk to ./data
    print("Copying apk file to " + os.path.join(os.path.curdir,'data') + "...")
    copy(apk_path, os.path.abspath("data"))

    new_apk_path = os.path.join('data', filename)
    
    #Decode apk using apktool and put output in ./data/output
    print("Decoding " + os.path.join(os.path.curdir, new_apk_path) + "...")
    try:
        subprocess.check_call(["apktool", "d", new_apk_path, "-o", output_dir, "-f"])
        #print("Success!")
    except subprocess.CalledProcessError as error:
        print("Something went wrong while decoding " + new_apk_path + " with apktool. Exit code: " + str(error.returncode))
    
    return os.path.abspath(output_dir)


