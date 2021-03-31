# Android-PHA-Scanner
Cybersecurity Project: Android PHA Scanner

## Requirements
- Python 3.8+ ([link](https://www.python.org/downloads/)) 
- apktool ([link](https://ibotpeaches.github.io/Apktool/install/))
- Install required python packages by running `pip install -r requirements.txt`
- spacy pipeline: `python -m spacy download en_core_web_sm`

## Usage
In the project directory:
`python3 main.py [COMMAND]`

For to get a list of available commands use:
`python3 main.py - --help`

For help with individual commands use:
`python3 main.py [COMMAND] --help`

## Project description
### Overview
This project is a potentially harmful app scanner targeting malware leveraging android accessibility services as described in [[1]](#1). The approach is based on a technique described by Diao et al. in 'Kindness is a Risky Business: On the usage of accessibility APIs in Android' section IV.3 [[2]](#2). Android apps that provide accessibility services are supposed to provide a human readable description for every such service, explaining what the accessibility capabilities are used for. The method for identifying potentially harmful apps relies on the fact that benign apps have no reason to provide a vague/fake description. Malicious apps however tend to provide very little helpful information in these descriptions as to what the accessibility capabilities are being used for, if they provide a description at all. Under this assumption, we flag an app as potentially harmful if it uses accessibility capabilities but fails to provide a sufficiently meaningful description of its services.

### How does it work?
The analysis consists of five main phases:
1) Decoding of the apk using apktool [[3]](#3). The decoded files are put in the temporary 'data' directory, which will be deleted once analysis is done.
2) Extraction of accessibility service description (and accessibility event types). For this task, several intermediary steps need to be taken: First we look at AndroidManifest.xml and find all accessibility services by checking if they declare the “BIND_ACCESSIBILITY_SERVICE” permission.  Next, we locate the accessibility services’ config files. From those we can learn what accessibility event types the app listens for, as well as the location of the accessibility service description in the strings.xml file. 
If this step fails, analysis will be aborted. If the app is found to make use of accessibility capabilities but no description can be found, we still flag it as potentially harmfull, assuming that simply no description was provided at all.
4) Part-of-Speech tagging: We use spaCy [[4]](#spacy), a natural language processing framework for python, to tag each word in a sentence with its role (verb, object, adjective, etc...). During this step, spaCy also builds a semantic relationship tree for each description, which is used in the next phase.
5) Action phrase extraction: Using the results from the previous step, we can now extract action phrases, i.e. verb + object combinations such as "save energy" or "perform gesture" by performing BFS starting from each verb in the description. Note that, similiarly to Diao et al. [[2]](#2), we ignore negated verbs in this step, as the actions will not be taken.
6) Categorization of the action phrases: Once we obtain a descriptions action phrase, we try to infer the described functionality by matching them against a set of rules for different types of functionalities. To make the matching less restrictive we also use stemmed forms of the action phrases as described in [[2]](#2). The rule sets were built heuristically, meaning that we looked at a large set of benign samples of accessibility services and for each apk, checked if it was correctly categorized. If not, the rules were modified/extended accordingly. The package names of the apps used for building the matching rules can be found in samples.csv. 
This process of building "good" rule sets is about deciding which stemmed action phrases should be adopted as rules for a given category, while trying to keep the size of each category's ruleset to a minimum, to avoid mismatching and increased runtime of the scanner.

If an app's functionality can not be categorized based on the description, it is flagged as potentially harmful.

### Structure
In this section we want to give an overview of the code's structure and highlight some points that might not be clear from looking at the in-code documentation:
- main.py: This script connects functionalities provided by the other scripts, but also to manage user interaction via the python Fire CLI. The analyze_apk function can be considered the main function of the program, as it contains the entire analysis loop. The analyze_directory function provides the same functionality as analyze_apk, just for an entire directory. Both can be executed via the CLI.
- decode_apk.py: This script provides all the functionality necessary to decode an apk with apktool. It does so by simply calling apktool as a subprocess and interacting with it as a user would do on the commandline.
- extract_features_from_xml.py: This script comprises all the functions that are used to extract various features from the decoded xml files contained in the apk file. More specifically, those features are: 
  - accessibility config files: those contain information the event accessibility event types the app listens for as well as the location of the accessibility service’s description.
  - Accessibility event types the app listens for
  - Accessibility service descriptions
  - Package name
- nlp_analysis.py: This script contains all the functions that revolve around processing the service descriptions, extracting action phrases and inferring the apps functionality from said action phrases.
- build_rules.py: This script basically does the same as running a directory analysis with the main.py script. The only difference is that it always prints descriptions, action phrases etc. and automatically moves apk files to different subdirectories depending on the scanning result. Its only purpose was used to make the process of building matching rules more efficient. Although it is not part of the scanner itself, we still decided to include it here, as it played a major role in the development process.

## Process Report and Results
To make it understandable how we came to the result, we want to explain our working process:
The task was to develop a PHA scanner for Android. Our initial approach was to use first static analysis to get an indication which apps could be malware by means of the code and afterwards use dynamic analysis to check the behaviour of the program at runtime. However, we decided against this approach because we didn't make a find in quest of tools for static and dynamic analysis. Furthermore, it would have been difficult to implement an entire dynamic analysis in the remaining time.
By reading lots of papers we found the final solution: The accessibility service description can be a hint on the malice of an app because malware often has a defective description. With Natural Language Processing (NLP) we can analyse this description and make a point about the app.
Then we started building the program: We began with the framework thus implemented functions that decode the apk and extract the relevant information from the apk. We defined the matching rules next and optimized these on and on. 
Finally, we tested our scanner on a set of malware samples and we were quite satisfied with the results: The scanner in its current form achieved surprisingly good False Negative rates, flagging only two of the 60 malware samples we had at our disposal as benign. False positive rates on the other hand turned out to be somewhat disappointing, which is unfortunate, but something we anticipated. Our scanner flagged 35 of the 149 benign samples (only including apps that actually use accessibility) as potentially harmful, resulting in a FPR of ~23%, which is relatively close to the 18.8% reported by Diao et al. [[2]](#2). Most of these false positives are however due to the lack of a meaningful description, rather than our scanner failing to infer an apps functionality from a meaningful description, implying that the scanner works as intended in an overwhelming majority of cases.

## Limitations
Of course, this approach has certain limitations, which we wanted to discuss in this section:
- spaCy trained models/pipelines: spaCy can perform its tasks based on different trained models and pipelines. These vary in complexity and thus accuracy. We decided to use the "en_core_web_sm" trained pipeline for PoS tagging and relationship extraction. This pipeline is designed more towards efficiency, which comes at a cost in accuracy. We chose this to keep the analysis more lightweight overall, but definitely noticed that the model occasionaly gets confused, which results in error in the PoS tagging. We tried to counteract some of those cases by sanitizing the descriptions, which, while certainly improving the results, couldn't solve all the issues.
- Heuristic approach/matching rules: Building rules heuristically, i.e. looking at individual samples, checking if they are correctly matched and if not, adjusting the matching rules accordingly, is a labour intensive and time consuming task. Machine learning classifiers would be an alternative solution though they might struggle with the limited size of service descriptions. Considering this as well as the limited amount of samples we would be able to acquire in the time we had left, we decided that the heuristic approach would probably yield better results.
- Finally, one could argue that malware authors can easily circumvent this method of scanning by providing a meaningful accessibility service description. As this is indeed a valid concern, we would like to briefly discuss this issue in the following section.

## Interpretation and (proposed) Future Work
In the case of a malware with a apparently meaningful description, it is reasonable to assume, that, while being meaningful in the sense of containing enough information to infer what functionality the app claims to have, the provided description will most likely still be fake, i.e. not describe what the app actually uses accessibility capabilities for.

While the scanner, in its current state, will not flag the app as potentially harmful, we can see it being extended with a module that allows it to check if the app's actual behavior matches what is claimed in the accessibility service description. Some form of dynamic analysis will probably be best suited for this task. The scanner already includes the functionality necessary for extracting which accessibility event types the app listens for. This knowledge could prove useful for such an extention, as accessibility events are commonly used by malware as triggers for their payload [[1]](#1).

## References
<a id="1">[1]</a> 
Kraunelis, Joshua & Chen, Yinjie & Ling, Zhen & Fu, Xinwen & Zhao, Wei. (2013). On Malware Leveraging the Android Accessibility Framework. ICST Transactions on Ubiquitous Environments. 1. 10.1007/978-3-319-11569-6_40. 

<a id="2">[2]</a> 
Diao, Wenrui & Zhang, Yue & Zhang, Li & Li, Zhou & Xu, Fenghao & Pan, Xiaorui & Xiangyu, Liu & Weng, Jian & Zhang, Kehuan & Wang, Xiaofeng. (2019). Kindness is a Risky Business: On the Usage of the Accessibility APIs in Android. https://www.researchgate.net/publication/334972024_Kindness_is_a_Risky_Business_On_the_Usage_of_the_Accessibility_APIs_in_Android

<a id="3">[3]</a>
https://ibotpeaches.github.io/Apktool/

<a id="spacy">[4]</a>
https://spacy.io/
