"""
Purpose: 
Use Breta for word detection, then pass cropped images using bboc into coMER for conversion to latex

Pre-execution instructions:
1) ensure structure is as such (edit ltr)
2) be at and make, folder one layer above src the working directory
3) install dependencies
    - `pip install numpy` || conda install -c anaconda numpy==1.16
    - `pip install pandas` || conda install -c anaconda pandas
    - `pip install opencv-python` || conda install -c conda-forge opencv
    - `pip install matplotlib` || conda install -c conda-forge matplotlib
    - conda install -c conda-forge gitpython
    - conda install -c conda-forge python-wget
    - conda install -c conda-forge scikit-image
    - conda install -c conda-forge scikit-learn  
    - conda install -c conda-forge tensorflow
    - conda install -c conda-forge miktex
    - python3.6
    
https://github.com/Wikunia/HE2LaTeX/blob/master/short_test.ipynb
https://github.com/Green-Wood/CoMER/blob/master/example/example.ipynb
https://github.com/Emmarex/Mathematical-Handwriting-recognition
https://github.com/PaulaZa5/latexer

Execution instructions: (sample)
python ./test/bretadecode.py
"""


# clone repo
import os

from git import Repo

git_url = "https://github.com/Breta01/handwriting-ocr.git"
repo_dir = "./download/breta-repo"
if not os.path.isdir(repo_dir):
    print("cloning repo...")
    Repo.clone_from(git_url, repo_dir)
print("repo ready in directory...")


# import dependencies
import sys

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf

sys.path.append(r"download\breta-repo\src")
from ocr import page, words
from ocr.helpers import implt

IMG = "output/ST2131_Tut1_T05_done/page13.jpg"
image = cv2.cvtColor(cv2.imread(IMG), cv2.COLOR_BGR2RGB)
crop = page.detection(image)
boxes = words.detection(crop)
lines = words.sort_words(boxes)


# clone repo
import os

from git import Repo

git_url = "https://github.com/Wikunia/HE2LaTeX.git"
repo_dir = "./download/h2l-repo"
if not os.path.isdir(repo_dir):
    print("cloning repo...")
    Repo.clone_from(git_url, repo_dir)
print("repo ready in directory...")


# load latex model
import numpy as np

sys.path.append(r"download\h2l-repo")
from Latex.Latex import Latex

mean_train = np.load("download/h2l-repo/train_images_mean.npy")
std_train = np.load("download/h2l-repo/train_images_std.npy")
model = Latex("model", mean_train, std_train, plotting=True)  # source of problem


# create directory required
import os
from os import listdir

path = "./output/latex"
if not os.path.isdir(path):
    os.mkdir(path)


# save image, output latex code
from skimage import io

document = []
lining = 0
item = 0
for line in lines:
    lining += 1
    line_content = []
    for (x1, y1, x2, y2) in line:
        item += 1
        # implt(crop[y1:y2, x1:x2])
        imgname = str(lining) + "-" + str(item)
        io.imsave("./output/latex/{}.jpg".format(imgname), crop[y1:y2, x1:x2])

        formula = io.imread("./output/latex/{}.jpg".format(imgname))
        formula = cv2.cvtColor(formula, cv2.COLOR_BGR2GRAY)
        correct = model.filename2formula(imgname)
        latex = model.predict(formula)
        line_content.append(latex["equation"])
        print("Seq: ", latex["equation"])
    document.append(line_content)
print(document)


# balance string
import copy


def balancedString(str):
    open, close, rm_c, rm_o = 0, 0, "", ""
    # remove extra close bracket
    for i in str:
        if i == "{":
            open += 1
        elif i == "}":
            close += 1
        if open >= close:
            rm_c = rm_c + i
        else:
            close -= 1
    # remove extra open bracket
    if open == close:
        if rm_c != "":
            return rm_c
        else:
            return str
    else:
        rev = rm_c[::-1]
        counter = 0
        for i in range(len(rev)):
            if counter < open - close:
                if rev[i] == "{":
                    counter += 1
                else:
                    rm_o = rm_o + rev[i]
            else:
                rm_o = rm_o + rev[i]
        return rm_o[::-1]


import os
import re
import subprocess

# convert latex code to pdf document
front = "\documentclass{article} \n \\begin{document} "
end = " \n \end{document}"
for eachline in document:
    temp = r""
    for pos in range(len(eachline)):
        working = eachline[pos].replace("#", "\\")
        working = working.replace("\\lt", "<")
        working = working.replace("\\gt", ">")
        if "frac" in working:
            if re.search(r"frac{[0-9]*}{[0-9]*}", working) is None:
                m = re.search("frac", working)
                p = m.span()[1]
                working = working[0:p] + r"{}" + working[p:]
        # print("working: ", working)
        # print("balance string: ", balancedString(working.strip()))
        if working.strip() != "":
            if pos == len(eachline) - 1:
                temp = temp + "\n" + balancedString(working.strip())
            else:
                temp = temp + "\n" + balancedString(working.strip()) + "\\\\"
    front = front + "\n \\begin{equation}" + temp + "\n \end{equation}"
latex_doc = front + end
print("CHECKPOINT")
print(latex_doc)
with open("simple.tex", "w") as f:
    f.write(latex_doc)
# cmd = ['pdflatex', '-interaction', 'nonstopmode', 'cover.tex']
cmd = ["pdflatex", "simple.tex"]
subprocess.run(cmd)

os.unlink("simple.tex")
os.unlink("simple.log")
os.unlink("simple.aux")


"""
https://stackoverflow.com/questions/57381430/synonym-of-type-is-deprecated-in-a-future-version-of-numpy-it-will-be-underst
https://blog.csdn.net/AugustMe/article/details/122192200
https://www.docx2latex.com/tutorials/mathematical-equations-latex/ # guide
"""
