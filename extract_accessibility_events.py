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

        print(config_path)
        config_path = config_path.replace('@', '')
        print(config_path)

        accessibility_config_file_paths.append(os.path.abspath(os.path.join(path, 'res', config_path + ".xml")))
    
    print(accessibility_config_file_paths)
    return accessibility_config_file_paths
#get_accessibility_config_files("/home/falckoon/cysecProj/Android-PHA-Scanner/data/output")

def extract_accessibility_events(config_file_list):
    for c in config_file_list:
        root = etree.parse(c).getroot()
        ns = root.nsmap
        event_types = root.get('{%(android)s}accessibilityEventTypes' % ns)
        print(event_types)

extract_accessibility_events(get_accessibility_config_files("/home/falckoon/cysecProj/Android-PHA-Scanner/data/output"))