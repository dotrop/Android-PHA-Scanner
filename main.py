#!/usr/bin/env python3

import decode_apk as dec
import extract_accessibility_events as extr

#Temporary for testing; Later input via CLI
#apk_path = "/home/falckoon/cysecProj/samples/mysterybot/51a9cd06be4b8f4217b0e64d3ac6b1d6"
apk_path = "/home/falckoon/cysecProj/samples/eventbot/7F5D728119951839B46895808107B281"

#Decode apk with apktool
decoded_apk_path = dec.decode(apk_path)

#Extract list of accessibility config files
accessibility_config_file_list = extr.get_accessibility_config_files(decoded_apk_path)

#Get dictionary of Event Types the app listens for
event_type_dict = extr.extract_accessibility_events(accessibility_config_file_list)

print("Static analysis done!")
print(event_type_dict)