#!/usr/bin/env python3

import os
from lxml import etree

class Error(Exception):
    pass

class NoManifestError(Error):
    pass

class NoEventTypesInMetaData(Error):
    pass


def get_accessibility_config_files(path):
    
    #Check if AndroidManifest.xml exists
    filename = os.path.join(path, "AndroidManifest.xml")
    if not os.path.exists(filename):
        raise NoManifestError

    root = etree.parse(filename).getroot()
    
    accessibility_config_file_paths = []
    
    ns = root.nsmap

    services = root.xpath("//service[@android:permission='android.permission.BIND_ACCESSIBILITY_SERVICE']", namespaces = ns)

    if not services:
        print("This app does not use any Accessibility services!")
        return None

    for s in services:
        meta_data = s.find("meta-data")
        if meta_data is None:
            continue
        else:
            config_path = s.find("meta-data").get('{%(android)s}resource' % ns)

            #Sanitize config_path
            config_path = config_path.replace('@', '')

            #Add config_path to list of config file paths
            accessibility_config_file_paths.append(os.path.abspath(os.path.join(path, 'res', config_path + ".xml")))
    
    return accessibility_config_file_paths

#Extract Accessibility Event Types from all accessibility config files
def extract_accessibility_events(config_file_list):
    
    #Dictionary keeping track of the presence of every possible event type constant in all of the apps accessibility config files
    event_type_dict = {
        "typeAllMask": False,
        "typeAnnouncement": False,
        "typeAssistReadingContext": False,
        "typeContextClicked": False,
        "typeGestureDetectionEnd": False,
        "typeGestureDetectionStart": False,
        "typeNotificationStateChanged": False,
        "typeTouchExplorationGestureEnd": False,
        "typeTouchExplorationGestureStart": False,
        "typeTouchInteractionEnd": False,
        "typeTouchInteractionStart": False,
        "typeViewAccessibilityFocusCleared": False,
        "typeViewAccessibilityFocused": False,
        "typeViewClicked": False,
        "typeViewFocused": False,
        "typeViewHoverEnter": False,
        "typeViewHoverExit": False,
        "typeViewLongClicked": False,
        "typeViewScrolled": False,
        "typeViewSelected": False,
        "typeViewTextChanged": False,
        "typeViewTextSelectionChanged": False,
        "typeViewTextTraversedAtMovementGranularity": False,
        "typeWindowContentChanged": False,
        "typeWindowStateChanged": False,
        "typeWindowsChanged": False
    }

    #go trough all accessibility config files
    for c in config_file_list:
        root = etree.parse(c).getroot()
        ns = root.nsmap

        #get string value of android:accessibilityEventTypes attribute
        for k, v in ns.items():
            try:
                atr_value = root.get('{{{}}}accessibilityEventTypes'.format(v))
            except KeyError:
                atr_value = None
                continue

        #Sanitize string and set presence in dict to True
        if atr_value is None:
            continue
        else:
            event_types = atr_value.split('|')
            for e in event_types:
                event_type_dict[e] = True

    #if typeAllMask=True, app listens for all accessibility event types. 
    if(event_type_dict["typeAllMask"]):
        for k, _ in event_type_dict.items():
            event_type_dict[k] = True
    
    listens_for_events = False
    for _, v in event_type_dict.items():
        if(v):
            listens_for_events = True

    if not listens_for_events:
        return None

    else:
        return event_type_dict

"""
    This function extracts and prints out an apps accessibility service description if one is available
    @return: List of description strings
"""
def extract_accessibility_service_descriptions(strings_xml_path, config_file_list):
    
    strings_root = etree.parse(strings_xml_path).getroot()
    desc_str_list = []
    
    #Iterate over all config files
    for c in config_file_list:
        root = etree.parse(c).getroot()
        ns = root.nsmap

        for k, v in ns.items():     #Iterate over namespace
            try:
                desc_str_name = root.get('{{{}}}description'.format(v))
            except KeyError:
                continue
            
            if desc_str_name is None:
                continue
            
            else:
                desc_str_name = desc_str_name.replace('@string/', '')       #strip @string/ part of the attributes value
                desc_list = strings_root.xpath('//string[@name="%s"]' % desc_str_name)  #Find string corresponding string in strings.xml
                for desc in desc_list:
                    desc_str_list.append(desc.text)
    
    #check if descriptions were extracted
    if not desc_str_list:
        return None

    return desc_str_list

def get_package_name(path):
    #Check if AndroidManifest.xml exists
    filename = os.path.join(path, "AndroidManifest.xml")
    if not os.path.exists(filename):
        raise NoManifestError

    root = etree.parse(filename).getroot()
    name = root.get('package')

    return name

                

        
            
        
    