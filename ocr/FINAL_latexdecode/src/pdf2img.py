"""
Purpose: 
Convert a single pdf file to multiple images

Pre-execution instructions:
1) ensure structure is as such
    - src
        - pdf2img.py
    - output
    - download
2) be at and make, folder one layer above src the working directory
3) install dependencies
    - pip install pdf2image || conda install -c conda-forge pdf2image
    - pip install matplotlib || conda install -c conda-forge matplotlib
    - pip install wget || conda install -c conda-forge python-wget
        - or manually download poppler (https://github.com/oschwartz10612/poppler-windows/releases/)
        - unzip poppler and take note of path e.g., /Download/poppler-XXX
        
Execution instructions: (sample)
python ./src/pdf2img.py -f "./download/original-data/1. Math Handwriting Recognition/Tutorial 01/ST2131_Tut1_t05_done.pdf" -o "./output"
"""


import getopt
# import packages
import os
import sys
import zipfile

import matplotlib.pyplot as plt
import wget
from pdf2image import convert_from_path
from pdf2image.exceptions import (PDFInfoNotInstalledError, PDFPageCountError,
                                  PDFSyntaxError)

# download files
if not os.path.isdir("./download/poppler-22.04.0"):
    url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v22.04.0-0/Release-22.04.0-0.zip"
    wget.download(url, out="./download")
    with zipfile.ZipFile("./download/Release-22.04.0-0.zip", "r") as zip_ref:
        zip_ref.extractall("download")
popplerpath = "./download/poppler-22.04.0/Library/bin"


def pdf2img(filepath, outputpath):
    """
    Summary:
        Take in 2 arguments to convert a single pdf file into multiple images (each being
        a page from the pdf of interest)
    Args:
        filepath (string): path to a single pdf file of interest [format: ./filename.pdf]
        outputpath (string): path to save output images from a single pdf [format: ./output]
    """
    # read in and convert pdf to image
    pages = convert_from_path(filepath, poppler_path=popplerpath)
    # create folder to store pdf specific output
    filename = filepath.split("/")[-1][:-4]
    print("filename:", filename)
    outputloc = outputpath + "/" + filename
    print("outputloc:", outputloc)
    if not os.path.exists(outputloc):
        # create a new directory because it does not exist
        os.makedirs(outputloc)
        print("output location created...")
    else:
        print("output location already exist...")
        # warn for possible overwriting
        while True:
            cont = input(
                "existing file in output location may be overwritten, continue [y]/n? "
            )
            if cont == "n" or cont == "y":
                break
            else:
                print("invalid response!")
        if cont == "n":
            print("append execution...")
            return
    # save pages
    for i in range(len(pages)):
        pages[i].save(outputloc + "/page" + str(i) + ".jpg", "JPEG")


def parsearg(argv):
    """
    Summary:
        Read in arguments given by command in cmd
    Args:
        argv (string): paths provided in cmd
    """
    # initialize variables
    arg_filepath = ""
    arg_outputpath = ""
    arg_help = "{0} -f <filepath> -o <outputpath>".format(argv[0])
    # read in arguments
    try:
        opts, args = getopt.getopt(
            argv[1:], "hf:o:", ["help", "filepath=", "outputpath="]
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
        elif opt in ("-f", "--filepath"):
            arg_filepath = arg
        elif opt in ("-o", "--outputpath"):
            arg_outputpath = arg
    # visualize arguments
    print("filepath:", arg_filepath)
    print("outputpath:", arg_outputpath)
    return arg_filepath, arg_outputpath


if __name__ == "__main__":
    import time

    start = time.process_time()
    fpath, opath = parsearg(sys.argv)
    pdf2img(fpath, opath)
    print("COMPLETED! runtime:", time.process_time() - start)


"""
Section specific references:
- [PDF Parsing](https://www.ismailmebsout.com/pdfs-parsing/)
- [Convert PDF to Image using Python](https://www.geeksforgeeks.org/convert-pdf-to-image-using-python/)
- [Poppler in path for pdf2image](https://stackoverflow.com/questions/53481088/poppler-in-path-for-pdf2image)
- [Unable to get page count. Is poppler installed in PATH?](https://github.com/Belval/pdf2image/issues/142)

FIN
"""
