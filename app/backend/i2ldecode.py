# import dependencies
import os
import re
import subprocess
import sys

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from pdf2image import convert_from_path
from skimage import io

# load utilities from git repo
sys.path.append(r"backend\download\breta-repo\src")
from ocr import page, words
from ocr.helpers import implt

# load latex model
sys.path.append(r"backend\download\h2l-repo")
from Latex.Latex import Latex

mean_train = np.load("backend/download/h2l-repo/train_images_mean.npy")
std_train = np.load("backend/download/h2l-repo/train_images_std.npy")
model = Latex("model", mean_train, std_train, plotting=True)


# detect page, then words and sort left -> right & up -> down
# input: image in numpy array
# output: (1) cropped image in numpy array (2) list of bbox coord
def get_words(img):
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    crop = page.detection(grey)
    boxes = words.detection(crop)
    lines = words.sort_words(boxes)
    return crop, lines


# input: (1) crop = image of page in numpy array (2) lines = list of bbox coord
# output: list of lists, inner list contain latex code for a line
def get_latex_code(crop, lines):
    document = []
    for line in lines:
        line_content = []
        for (x1, y1, x2, y2) in line:
            formula = cv2.cvtColor(crop[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
            latex = model.predict(formula)
            line_content.append(latex["equation"])
        document.append(line_content)
    return document


# balance string
# input: str
# output: str
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


# naive correction for broken latex code (1) replace #, lt, gt (2) check frac{}{} format
# input: list of lists, inner list contain latex code for a line
# output: list of lists, inner list contain latex code for a line
def debug_latex(document):
    correct_document = []
    for eachline in document:
        correct_line = []
        for pos in range(len(eachline)):
            working = eachline[pos].replace("#", "\\")
            working = working.replace("\\lt", "<")
            working = working.replace("\\gt", ">")
            if "frac" in working:
                if re.search(r"frac{[0-9]*}{[0-9]*}", working) is None:
                    m = re.search("frac", working)
                    p = m.span()[1]
                    working = working[0:p] + r"{}" + working[p:]
            if working.strip() != "":
                correct_line.append(balancedString(working.strip()))
        correct_document.append(correct_line)
    return correct_document


# compile latex code
# input: list of lists, inner list contain latex code for a line
# output: str
def compile_latex(correct_document):
    front = "\documentclass{article} \n \\begin{document}"
    end = " \n \end{document}"
    counter = 0
    for line in correct_document:
        temp = r""
        for item in line:
            temp = temp + "\n" + item
        text_file = open("./backend/output.{}.txt".format(counter), "w")
        text_file.write(temp)
        text_file.close()
        counter += 1
        front = front + "\n \\begin{equation}" + temp + "\n \end{equation}"
    return front + end


# compress pipeline into one place
# input: image in numpy array
def i2l_decode(image):
    print("conversion start...")
    crop, lines = get_words(image)
    print("found words...")
    code = get_latex_code(crop, lines)
    print("got latex...")
    correct_code = debug_latex(code)
    print("debug latex...")
    compiled_code = compile_latex(correct_code)
    print("compile code...")

    # write latex file
    print("converting to pdf...")
    with open("temp.tex", "w") as f:
        f.write(compiled_code)
    # convert latex to pdf
    cmd = ["pdflatex", "temp.tex"]
    subprocess.run(cmd)
    os.unlink("temp.tex")
    os.unlink("temp.log")
    os.unlink("temp.aux")

    # convert pdf to image
    print("converting pdf to image...")
    pdf_image = convert_from_path("temp.pdf")
    os.remove("temp.pdf")
    return pdf_image


"""
"""
# for local check
def Main(imgpath):
    img = cv2.imread(imgpath)
    output = i2l_decode(img)
    # print(type(output))
    # print(output)
    cv2.imwrite("backend/result/latex-temp.jpg", np.array(output[0]))


Main("backend/image/0.jpg")
