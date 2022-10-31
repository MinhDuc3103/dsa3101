from pickle import FALSE

import cv2
import easyocr
import numpy as np
from matplotlib import pyplot as plt

IMAGE_PATH = "modified-data/page0.jpg"
reader = easyocr.Reader(["en"], gpu=False)
result = reader.readtext(IMAGE_PATH)
for i in result:
    print(i[1])
