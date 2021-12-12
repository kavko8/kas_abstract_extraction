This repository contains source code and install instructions for extracting abstracts from slovene academic .pdf texts (BSc MSc and PhD). This code extracts the abstarct in english and slovenian language.


#### Prerequisites
- Docker
- Linux OS
- (opt.) python3
- (opt.) python3 virtual environment

Please refere to https://docs.docker.com/get-docker/ for install instructions

#### Usage
WITH DOCKER:
- git clone https://github.com/kavko8/kas_abstract_extraction.git
- cd kas_abstract_extraction
- docker build -t abstract_extract .
- docker run -it -v ABS_PATH_TO_FOLDER_CONTAINING_PDF:/PDF --name abstract_extract abstract_extract:latest
- This should make two new directories nammed "kas_en" and "kas_sl" in your ABS_PATH_TO_FOLDER_CONTAINING_PDF containing abstracts in .txt format
  
WITHOUT DOCKER:
- git clone https://github.com/kavko8/kas_abstract_extraction.git
- cd kas_abstract_extraction/abstract
- mkdir PDF
- place your .pdf files in the newly created PDF folder
- python3 -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt
- python3 main.py