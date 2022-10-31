"""
Purpose: 
OCR using Pytesseract
The approach is basically just rely on one provider for everything
Known to work well only for typed words

Pre-execution instructions:
1) ensure structure is as such
    - src
        - pdf2img.py
        - splitdoc.py
        - pytedecode.py
    - output
    - download
2) be at and make, folder one layer above src the working directory
3) install dependencies
    - `pip install re` || conda install -c conda-forge regex
    - `pip install pytesseract` || conda install -c conda-forge pytesseract tesseract
        
Execution instructions: (sample)
python ./src/splitdoc.py -f "./output/ST2131_Tut1_T05_done/temp" -l "eng+equ"
"""


import getopt
import re
import sys
# import packages
from cgi import print_form

import cv2
import numpy as np
import pytesseract
from pytesseract import Output

# tell pytesseract where the engine is installed, use `where tesseract` to help out
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\20jam\anaconda3\envs\pipeline\Library\bin\tesseract.exe"
)


# extract text from image with two columns of contents
def extractTextFromImg(segment, language):  # 'eng'
    """
    Summary:
        Extract text from image provided
    Args:
        segment (image): segmented images
        language (string): language which pytesseract engine should use
    Returns:
        string: contents decoded from image feed into the function
    """
    text = pytesseract.image_to_string(segment, lang=language)
    text = text.encode("gbk", "ignore").decode("gbk", "ignore")
    return text


def binarization(img):
    """
    Summary:
        Binarize images
    Args:
        img (image): image to binarize (segmented images)
    Returns:
        thresh (integer): threshold
        im_bw (image): output image that is binarized
    """
    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh, im_bw = cv2.threshold(gray_image, 210, 230, cv2.THRESH_BINARY)
    return thresh, im_bw


def noise_removal(image):
    """
    Summary:
        Remove noise in imagw
    Args:
        image (image): image to remove noise from
    Returns:
        image (image): output image that had noise removed
    """
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.dilate(image, kernel, iterations=1)
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.erode(image, kernel, iterations=1)
    image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    image = cv2.medianBlur(image, 3)
    return image


def thin_font(image):
    """
    Summary:
        Errosion and dilation, i.e., to remove bolded parts in fonts
    Args:
        image (image): image to do font thining
    Returns:
        image (image): image with word fonts thinned
    """
    image = cv2.bitwise_not(image)
    kernel = np.ones((2, 2), np.uint8)
    image = cv2.erode(image, kernel, iterations=1)
    image = cv2.bitwise_not(image)
    return image


def parsearg(argv):
    """
    Summary:
        Read in arguments given by command in cmd
    Args:
        argv (string): paths provided in cmd
    """
    # initialize variables
    arg_folderpath = ""
    arg_lang = ""
    arg_help = "{0} -f <folderpath> -l <lang>".format(argv[0])
    # read in arguments
    try:
        opts, args = getopt.getopt(
            argv[1:], "hf:l:", ["help", "arg_folderpath=", "lang="]
        )
    except:  # return help and error message
        print(arg_help)
        sys.exit(2)
    # parse arguments
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            # print the help message
            print(arg_help)
            sys.exit(2)
        elif opt in ("-f", "--folderpath"):
            arg_folderpath = arg
        elif opt in ("-l", "--lang"):
            arg_lang = arg
    # visualize arguments
    print("folderpath:", arg_folderpath)
    print("lang:", arg_lang)
    return arg_folderpath, arg_lang


if __name__ == "__main__":
    import time

    start = time.process_time()
    fpath, lang = parsearg(sys.argv)

    import os

    segmentpaths = []
    for filename in os.listdir(fpath):
        reg = re.compile(r"^[0-9]+\.jpg$")
        if reg.match(filename):
            segmentpaths.append(fpath + "/" + filename)
    print(segmentpaths)

    contents = []
    for parts in segmentpaths:
        img = cv2.imread(parts)
        # preprocessing images in segment list (optional)
        # thresh, img = binarization(img)
        # img = noise_removal(img)
        # img = thin_font(img)
        contents.append(extractTextFromImg(img, lang))

    with open(fpath + "/contents.txt", "w") as fp:
        print("OCR at work, converting image to text...")
        for item in contents:
            # write each item on a new line
            fp.write("%s\n" % item)

    print("COMPLETED! runtime:", time.process_time() - start)


"""
Section specific references:
- [Printedand handwritten text extraction from images using Tesseract and Google Cloud Vision API](https://medium.com/@derrickfwang/printed-and-handwritten-text-extraction-from-images-using-tesseract-and-google-cloud-vision-api-ac059b62a535)
- [HandwritingRecognition_GoogleCloudVision](https://github.com/DerrickFeiWang/HandwritingRecognition_GoogleCloudVision/blob/master/OCR_Printed%20and%20handwritten%20text%20extraction%20from%20images%20using%20Tesseract%20and%20Google%20Cloud%20Vision%20API_20200805.ipynb)
- [Image Preprocessing for Pytesseract](https://www.youtube.com/watch?v=ADV-AjAXHdc)
- [OC Python Textbook](https://github.com/wjbmattingly/ocr_python_textbook/blob/main/02_02_working%20with%20opencv.ipynb)
- [Pytesseract Installation on Anaconda](https://pythonforundergradengineers.com/how-to-install-pytesseract.html)
- [Improving Quality of Output for Pytesseract](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html)
- [Image Preprocessing for Pytesseract](https://www.youtube.com/watch?v=ADV-AjAXHdc)

FIN
"""
