#!/usr/bin/env python3

from googletrans import Translator
import spacy

def translate_descriptions(desc_list):
    translator = Translator()
    translation = []
    for desc in desc_list:
        translation.append(translator.translate(desc, dest='de'))

    english_descriptions = [t.text for t in translation]
    return english_descriptions