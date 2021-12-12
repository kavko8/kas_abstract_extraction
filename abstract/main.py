import os
import shutil

os.makedirs("./figures")
os.makedirs("./figures_txt")
try:
    print("1/4 - Extracting figures")
    os.system("python3 extract_figures.py")
    print("2/4 - Extracting whole tekst")
    os.system("python3 extract_txt.py")
    print("3/4 - Extracting slovenian abstract")
    os.system("python3 extract_abs_sl.py")
    print("4/4 - Extracting english abstract")
    os.system("python3 extract_abs_en.py")

except:
    pass

print("DONE - look in the folder containing .pdf files - there should be two new folders containing abstracts.")
shutil.rmtree("./figures")
shutil.rmtree("./figures_txt")
