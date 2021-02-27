#!/usr/bin/env python3

import os
from lxml import etree

class Error(Exception):
    pass

class NoManifestError(Error):
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

    for s in services:
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
        atr_value = root.get('{%(android)s}accessibilityEventTypes' % ns)

        #Sanitize string and set presence in dict to True
        event_types = atr_value.split('|')
        for e in event_types:
            event_type_dict[e] = True

    #if typeAllMask=True, app listens for all accessibility event types. 
    if(event_type_dict["typeAllMask"]):
        for k, v in event_type_dict.items():
            event_type_dict[k] = True

    return event_type_dict
    