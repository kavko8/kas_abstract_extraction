import re
import subprocess
from itertools import groupby
import pdftotext
import os
from natsort import natsorted
from polyglot.detect import Detector
from polyglot.detect.base import logger as polyglot_logger
import tqdm
from pdf2image import convert_from_path
import numpy as np
import cv2
from cdifflib import CSequenceMatcher

SequenceMatcher = CSequenceMatcher


polyglot_logger.setLevel("ERROR")


toc_idx = {
    "kazalo": ["kazalo", "vsebina", "kazalo vsebine"],
    "kljucne": ["ključne besede", "kljucne besede", "ključne", "kljucne", "ključni"],
    "povzetek": ["povzetek", "izvlecek", "izvleček"],
    "ostala kazala": ["kazalo slik", "seznam slik", "kazalo tabel", "seznam tabel"],
    "abstracts": ["abstract", "summary"],
    "besede": ["besede", "besede:", "pojmi"]
}


def similar(a: str, b: str, conf: float = 0.6):
    ratio = SequenceMatcher(None, a, b).ratio()
    similarity = True if ratio >= conf else False
    return similarity


def check_language(text: str, lang: str = "sl", conf: int = 70):
    l = False
    language = Detector(text, quiet=True)
    if language.languages[0].code == lang:  # check  the first language (highest percentage) of the output
        if int(language.languages[0].confidence) > conf:
            l = True
    return l


def calculate_crop_area(pdf_name, index):

    images = convert_from_path(pdf_name, dpi=72)  # , last_page=15)
    img = np.array(images[index])

    offset = 0
    bottom = img.shape[0]

    gray = gray_img(img)
    thresh = otsu_img(gray)
    if is_white(thresh):
        thresh = invert_img(thresh)[0:120, 0:img.shape[1]]
    cnts = search_contours(thresh)
    if len(cnts):
        cnts.sort(key=lambda c: cv2.boundingRect(c)[2])
        cnt = cnts[-1]
        x, y, width, height = cv2.boundingRect(cnt)
        if width > img.shape[1]//2:
            offset = y + height
    if not offset:
        kernel = np.ones((15, img.shape[1]//2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cnts = search_contours(thresh)
        if len(cnts):
            cnts.sort(key=lambda c: cv2.boundingRect(c)[2])
            cnt = cnts[-1]
            x, y, width, height = cv2.boundingRect(cnt)
            if abs(width - height) < 20:
                offset = y + height

    thresh = otsu_img(gray)
    if is_white(thresh):
        thresh = invert_img(thresh)[img.shape[0]-250:img.shape[0], 0:img.shape[1]]
    kernel = np.ones((2, 16), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    cnts = search_contours(thresh)
    if len(cnts):
        cnts.sort(key=lambda c: cv2.boundingRect(c)[1], reverse=True)
        for cnt in cnts:
            x, y, width, height = cv2.boundingRect(cnt)
            if abs(width - height) < 50 or (width > img.shape[1]//2 and height < 5):
                bottom = img.shape[0] - 250 + y - 1
                break

    #if pdf_name == "/home/matic/Desktop/pdfji/kas-4222.pdf":
    #    cv2.imshow("thr", thresh)# np.array(images[9])[offset:bottom, 0:img.shape[1]])
    #    cv2.imshow("img", img[offset:bottom, 0:img.shape[1]])
    #    cv2.waitKey(0)
    #    cv2.destroyAllWindows()
    return offset, bottom


def invert_img(img):
    return cv2.bitwise_not(img)


def gray_img(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def otsu_img(gray):
    return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]


def search_contours(thresh):
    return cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]


def is_white(img):
    return True if np.sum(img == 255) > np.sum(img == 0) else False

def get_abs_index(pdf_name):

    #pdf = subprocess.check_output(
    #    f'pdftotext -layout -enc "UTF-8" -q {pdf_name} -',
    #    shell=True,
    #    encoding="UTF-8")
    pdf = open(pdf_name).read()
    pdf = pdf.split("\f")
    abs_index = len(pdf)//2
    for index, page in enumerate(pdf):
        lines = page.split("\n")
        for line_index, line in enumerate(lines):
            # if index > 5 and pdf_name == "/home/matic/Desktop/pdfji2/kas-7791.pdf":
            #    neki = "hdh
            while line.startswith(" "):
                line = line[1:]
            while line.endswith(" "):
                line = line[:-1]
            if len(line) < 20:
                # if line.count(".") < 3 and line.count("_") < 3 and line.count(" ") < 5 and len(line) < 20:
                first_word = re.sub(r"\d", "", line)
                first_word = first_word.replace(".", "")

                words = first_word.split(" ")
                if name == "kas-36054.pdf":
                    a = "a"
                if len(words) < 5:
                    for w in words:
                        if len(w):
                            first_word = w.replace(" ", "").lower()
                            for mark in toc_idx["povzetek"]:
                                if not first_word.isdigit():
                                    similarity = similar(first_word, mark, conf=0.85)
                                    if similarity:
                                        abs_index = index
                                        break
    return abs_index

def ai(pdf_name):
    pdf = open(pdf_name).read()
    lines = pdf.split("\n")
    povzetek = -1
    udk = -1
    kljuce_besede = -1
    izvlecek = -1
    nums = [i for i in range(10)]
    found = False
    count = 0
    index = -1
    found2 = False
    text = None
    for j, line in enumerate(lines):
        l = line.replace(" ", "")
        l = l.lower()
        l = l.replace("č", "c")
        if "kljucnadokumentacijskainformacija" in l and l.endswith("a"):
            found = True
        if found:
            if count < 20:
                count += 1
                if line.startswith("AI"):
                    index = j
                    found2 = True
                    break
            else:
                break

    if found2:
        lines = lines[index:]
        text = ""
        ends = [".", "!", "?", "…"]
        for j, line in enumerate(lines):
            if j == 0:
                line = line.replace("AI", " ")
                if len(line):
                    try:
                        while line[0] == " ":
                            line = line[1:]
                    except IndexError:
                        pass
                    text = text + line + " "
            else:
                if not len(line):
                    break
                else:
                    if len(line.split()) < 6 and line[-1] not in ends:
                        break
                    else:
                        text = text + line + " "
    return text




# Load your PDF


# If it's password-protected
#with open("secure.pdf", "rb") as f:
#    pdf = pdftotext.PDF(f, "secret")

# How many pages?
#print(len(pdf))

# Iterate over all the pages
#for page in pdf:
#    print(page)

# Read some individual pages
#print(pdf[0])
#print(pdf[1])

# Read all the text into one string
#print("\n\n".join(pdf))
base_name = "./kas_new_text"
os.makedirs("./povzetki_all", exist_ok=True)
import pandas as pd
meta = pd.read_table(f"./kas-meta.tbl", sep="\t")  # dataframe of KAS_no_abs metadata


def remove_noise(txt):
    txt = re.sub('[\u000B\u000C\u000D\u0085\u2028\u2029]+', '', txt)
    txt = re.sub(" +", " ", txt)
    txt = txt.replace("²", "š")
    txt = txt.replace("£", "č")
    txt = txt.replace("\uf0b7", "-")
    txt = txt.replace("•", "-")
    txt = txt.replace("ţ", "ž")
    txt = txt.replace("Ţ", "Ž")
    txt = txt.replace("Ċ", "Č")
    txt = txt.replace("ċ", "č")
    txt = txt.replace("", "")
    txt = txt.replace("\t", "")
    txt = txt.replace("", "-")
    txt = txt.replace("\u000C", "")
    return txt
    


sum_count = tqdm.tqdm(total=len(os.listdir(base_name)))
with sum_count as s_c:
    for j, name in enumerate(natsorted(os.listdir(base_name))):
        pdf_name = os.path.join(base_name, name)
        #with open(pdf_name, "rb") as f:
        #    pdf = pdftotext.PDF(f)
        title = meta.loc[meta["id"] == name.replace(".txt", "")]["title"].tolist()
        if len(title):
            title = title[0]
        else:
            title = "UNKNOWNUNKNOWNUNKNOWN"
        a = ai(pdf_name)

        if a is None:
            if "kas" in name:
                pdf = open(pdf_name).read()
                pdf = pdf.split("\n")
                pdf = [line for line in pdf if len(line)]
                abs_index = -1
                kw_index = -1
                text = ""
                for ind, line in enumerate(pdf):
                    numbers = sum(c.isdigit() for c in line)
                    l = line.lower().replace(" ", "")
                    l = re.sub(f"\d", "", l)

                    if similar(l, "povzetek", 0.9) and ":" not in l and numbers<2:
                        abs_index = ind + 1

                if abs_index < 0:
                    for ind, line in enumerate(pdf):
                        l = line.lower().replace(" ", "").replace("č", "c")
                        l = re.sub(f"\d", "", l)
                        if similar(l, "izvlecek", 0.9) and "izvleckov" not in l:
                            abs_index = ind + 1


                if abs_index > 0:
                    pdf = pdf[abs_index:]
                    text = ""
                    ends = [".", "!", "?", "…", ":", ";", ",", "-"]

                    for j, line in enumerate(pdf):
                        if len(line) > 1:
                            stoph = line.lower().replace(" ", "").replace(".", "")
                            stoph = re.sub("\d", "", stoph)
                            kb = stoph[0:14]
                            kw = stoph[0:9]
                            ab = stoph[0:9]
                            suma = stoph[0:8]
                            if "kas-3607" in name:
                                a="a"
                            if similar("kljucnebesede", kb, 0.8):
                                break
                            if similar("keywords", kw, 0.8):
                                break
                            if similar("abstarct", ab, 0.8):
                                break
                            if similar("summary", suma, 0.8):
                                break
                            if len(line.split()) < 6 and line[-1] not in ends and not line.replace(" ", "").startswith("-") and sum(c.isdigit() for c in line.replace(" ", "")) != len(line.replace(" ", "")):
                                break

                            if title.lower() not in line.lower() and "UDK" not in line:
                                temp_l = line.split()
                                temp_l = [l for l in temp_l if sum(c.isdigit() for c in l) == 0]
                                temp_l = "".join(temp_l)
                                if temp_l.replace(" ", "").isupper() and not line[-1] in ends:
                                    pass
                                else:
                                    if sum(c.isdigit() for c in line.replace(" ", "")) != len(line.replace(" ", "")):
                                        if not line.lower().startswith("naslov:") and not line.lower().replace(" ", "").startswith("predmetneoznake:"):
                                            slash = line.count("/")
                                            if slash < 4:
                                                text = text + line + " "


                if len(text) > 200:
                    abs_text = remove_noise(text)
                    with open(f"./povzetki_all/{name.replace('.txt', '-abs-sl.txt')}", "w") as f:
                        f.writelines(abs_text[:-1])
                        f.close()
        else:
            with open(f"./povzetki_all/{name.replace('.txt', '-abs-sl.txt')}", "w") as f:
                f.writelines(a)
                f.close()
        s_c.update(1)
        s_c.refresh()
