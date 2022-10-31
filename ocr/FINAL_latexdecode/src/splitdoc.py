"""
Purpose: 
Split page into sections, ideally separating the written and types in the image

Pre-execution instructions:
1) ensure structure is as such
    - src
        - pdf2img.py
        - splitdoc.py
    - output
    - download
2) be at and make, folder one layer above src the working directory
3) install dependencies
    - `pip install opencv-python` || conda install -c conda-forge opencv
    - `pip install pandas` || conda install -c anaconda pandas
    - `pip install numpy` || conda install -c anaconda numpy
    - `pip install pandasql` || conda install -c anaconda pandasql
        
Execution instructions: (sample)
python ./src/splitdoc.py -f "./output/ST2131_Tut1_T05_done"
"""


import getopt
# import packages
import os
import sys

import cv2
import pandas as pd
import pandasql as ps

fileList = []


# crop image
def pageSegmentation1(imgpath, w, df_SegmentLocations):
    """
    Summary:
        Crop image using structure-lines of images found
    Args:
        imgpath (string): path to image
        w (integer): number of rows the image is split into
        df_SegmentLocations (dataframe): df containing position to segment image
    Returns:
        images: images split into its segments
    """
    img = cv2.imread(imgpath)
    im2 = img.copy()
    segments = []

    # create directory to store output images
    storagepath = "/".join(imgpath.split("/")[:-1]) + "/temp/"
    print("storagepath:", storagepath)
    if not os.path.exists(storagepath):
        os.mkdir(storagepath)

    for i in range(len(df_SegmentLocations)):
        y = df_SegmentLocations["SegmentStart"][i]
        h = df_SegmentLocations["Height"][i]
        cropped = im2[y : y + h, 0:w]
        segments.append(cropped)
        cv2.imwrite(storagepath + "/{}.jpg".format(i + 1), cropped)
    return segments


# page segmentation
def findHorizontalLines(imgpath):
    """
    Summary:
        Find structure of page using lines useful if
            - question paper separate sections with lines
            - writing paper has line grids
    Args:
        imgpath (string): path to a single image
    Returns:
        image: image containing lines extracted from images
    """
    img = cv2.imread(imgpath)
    # create directory to store output images
    storagepath = "/".join(imgpath.split("/")[:-1]) + "/temp/"
    print("storagepath:", storagepath)
    if not os.path.exists(storagepath):
        os.mkdir(storagepath)
    # convert image to greyscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(storagepath + "/gray.jpg", gray)
    # set threshold to remove background noise
    thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    cv2.imwrite(storagepath + "/thresh.jpg", thresh)
    # define rectangle structure (line) to look for: width 100, hight 1. this is a
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (200, 1))
    cv2.imwrite(storagepath + "/hkernel.jpg", horizontal_kernel)
    # find horizontal lines
    lineLocations = cv2.morphologyEx(
        thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1
    )
    cv2.imwrite(storagepath + "/lLoc.jpg", lineLocations)
    return lineLocations


# read in images
def readImg(folderpath):
    """
    Summary:
        Read in the output images from pdf2img.py
    Args:
        folderpath (string): path to list of images outputted from pdf2img.py
    """
    # compile image path in a list
    global fileList
    fileList = [
        folderpath + "/" + x for x in os.listdir(folderpath) if "jpg" in x.lower()
    ]


def parsearg(argv):
    """
    Summary:
        Read in arguments given by command in cmd
    Args:
        argv (string): paths provided in cmd
    """
    # initialize variables
    arg_folderpath = ""
    arg_help = "{0} -f <folderpath>".format(argv[0])
    # read in arguments
    try:
        opts, args = getopt.getopt(argv[1:], "hf:", ["help", "folderpath="])
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
    # visualize arguments
    print("folderpath:", arg_folderpath)
    return arg_folderpath


if __name__ == "__main__":
    import time

    start = time.process_time()
    fpath = parsearg(sys.argv)
    readImg(fpath)

    imgpath = fileList[5]  # one page for now
    lineLocations = findHorizontalLines(imgpath)
    w = lineLocations.shape[1]

    # formatting lines
    df_lineLocations = pd.DataFrame(lineLocations.sum(axis=1)).reset_index()
    df_lineLocations.columns = ["rowLoc", "LineLength"]
    df_lineLocations["line"] = 0
    df_lineLocations["line"][df_lineLocations["LineLength"] > 100] = 1
    df_lineLocations["cumSum"] = df_lineLocations["line"].cumsum()

    # query lines
    query = """
    select row_number() over (order by cumSum) as SegmentOrder
    , min(rowLoc) as SegmentStart
    , max(rowLoc) - min(rowLoc) as Height
    from df_lineLocations
    where line = 0
    --and CumSum != 0
    group by cumSum
    """
    df_SegmentLocations = ps.sqldf(query, locals())

    # segment images
    segments = pageSegmentation1(imgpath, w, df_SegmentLocations)

    print("COMPLETED! runtime:", time.process_time() - start)


"""
Section specific references:
- [Printedand handwritten text extraction from images using Tesseract and Google Cloud Vision API](https://medium.com/@derrickfwang/printed-and-handwritten-text-extraction-from-images-using-tesseract-and-google-cloud-vision-api-ac059b62a535)
- [HandwritingRecognition_GoogleCloudVision](https://github.com/DerrickFeiWang/HandwritingRecognition_GoogleCloudVision/blob/master/OCR_Printed%20and%20handwritten%20text%20extraction%20from%20images%20using%20Tesseract%20and%20Google%20Cloud%20Vision%20API_20200805.ipynb)

FIN
"""
