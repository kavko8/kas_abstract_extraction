import pandas as pd
import re
import os
from natsort import natsorted
import tqdm
import numpy as np
from cdifflib import CSequenceMatcher

SequenceMatcher = CSequenceMatcher


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


def ai(pdf_name):
    pdf = open(pdf_name).read()
    lines = pdf.split("\n")
    found = False
    count = 0
    index = -1
    found2 = False
    text = None
    for j, line in enumerate(lines):
        l = line.replace(" ", "")
        l = l.lower()
        l = l.replace("č", "c")
        if similar("keywordsdocumentation", l, 0.9) and l.endswith("n"):
            found = True
        if found:
            if count < 20:
                count += 1
                if line.startswith("AB"):
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
                line = line.replace("AB", " ")
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


fold = "abs-en"
base_name = "./figures_txt"
os.makedirs(f"./PDF/{fold}", exist_ok=True)


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

        title = "UNKNOWNUNKNOWNUNKNOWN"
        a = ai(pdf_name)
        if a is None:
            try:
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
                    l = re.sub('\x0c', "", l)

                    if similar(l, "abstract", 0.9) and ":" not in l and numbers < 2:
                        abs_index = ind + 1
                        break

                if abs_index < 0:
                    for ind, line in enumerate(pdf):
                        l = line.lower().replace(" ", "").replace("č", "c")
                        l = re.sub(f"\d", "", l)
                        l = re.sub('\x0c', "", l)
                        if similar(l, "summary", 0.9):
                            abs_index = ind + 1
                            break

                if abs_index > 0:
                    pdf = pdf[abs_index:]
                    text = ""
                    ends = [".", "!", "?", "…", ":", ";", ",", "-"]

                    for j, line in enumerate(pdf):
                        if len(line) > 1:
                            stoph = line.lower().replace(" ", "").replace(".", "")
                            stoph = re.sub("\d", "", stoph)
                            stoph = re.sub('\x0c', "", stoph)
                            kb = stoph[0:14]
                            kw = stoph[0:9]
                            ab = stoph[0:9]
                            the_kw = stoph[0:12]
                            if similar("keywords", kw, 0.8) or similar("ključnebesede", kb, 0.8) or similar("povzetek", ab, 0.8) or similar("thekeywords:", the_kw, 0.95) and j > 1:
                                break
                            if len(line.split()) < 6 and line[-1] not in ends and not line.replace(" ", "").startswith("-") and sum(c.isdigit() for c in line.replace(" ", "")) != len(line.replace(" ", "")) and j > 1:
                                break

                            if title.lower() not in line.lower() and "UDC" not in line:
                                temp_l = line.split()
                                temp_l = [l for l in temp_l if sum(
                                    c.isdigit() for c in l) == 0]
                                temp_l = "".join(temp_l)
                                if temp_l.replace(" ", "").isupper() and not line[-1] in ends:
                                    pass
                                else:
                                    if sum(c.isdigit() for c in line.replace(" ", "")) != len(line.replace(" ", "")):
                                        if not line.lower().startswith("title:") and not line.lower().replace(" ", "").startswith("subjecttags:"):
                                            slash = line.count("/")
                                            if slash < 4:
                                                text = text + line + " "

                    if len(text) > 200:
                        abs_text = remove_noise(text)
                        with open(f"/PDF/{fold}/{name.replace('.txt', '-abs-en.txt')}", "w") as f:
                            f.writelines(abs_text[:-1])
                            f.close()
            except:
                pass
        else:
            with open(f"/PDF/{fold}/{name.replace('.txt', '-abs-en.txt')}", "w") as f:
                f.writelines(a)
                f.close()
        s_c.update(1)
        s_c.refresh()
