"""
Purpose: 
Detect text, arrange bounding boxes, textline detection, img to latex

Pre-execution instructions:
1) ensure structure is as such (edit ltr)
2) be at and make, folder one layer above src the working directory
3) install dependencies
    - `pip install numpy` || conda install -c anaconda numpy
    - `pip install pandas` || conda install -c anaconda pandas
    - `pip install opencv-python` || conda install -c conda-forge opencv
    - `pip install matplotlib` || conda install -c conda-forge matplotlib
    - `pip install tqdm` || conda install -c conda-forge tqdm
    - conda install -c conda-forge tensorflow
    - conda install -c conda-forge scikit-learn
    - conda install -c conda-forge keras
    - conda install scipy
    - conda install -c conda-forge gitpython
    - conda install -c conda-forge python-wget
4) download pretrained model manually and put in ./download/yolo-repo/model/text-detect.h5
    - https://drive.google.com/file/d/1OwrEu6SeaNM3l_clLN9F40W-tMpRfz97/view
    - unable to automate this, so in deployment, transfer of file using volume will be required

Execution instructions: (sample)
python ./test/mulsrcdecode.py
"""


# clone repo
import os

from git import Repo

git_url = "https://github.com/Neerajj9/Text-Detection-using-Yolo-Algorithm-in-keras-tensorflow.git"
repo_dir = "./download/yolo-repo"
if not os.path.isdir(repo_dir):
    print("cloning repo...")
    Repo.clone_from(git_url, repo_dir)
print("repo ready in directory...")


# variable definition
img_w = 512
img_h = 512
channels = 3
classes = 1
info = 5
grid_w = 16
grid_h = 16


from keras.models import model_from_json


def load_model(path):
    """
    Summary:
    Load pretrained model
    Args:
        path (string): path to pretrained model (model in json format)
    Returns:
        model instance: parsed model
    """
    print("opening model json file...")
    json_file = open(path, "r")
    print("reading model json file...")
    loaded_model_json = json_file.read()
    json_file.close()
    print("parsing model json file...")
    loaded_model = model_from_json(loaded_model_json)
    print("completed!")
    return loaded_model


import sys

import cv2
import matplotlib.pyplot as plt

sys.path.append("./download/yolo-repo")
from Utils import decode


def predict_func(model, inp, iou, name):
    """
    Summary:
    Predict position of words using pretrained model and save result
    Args:
        model (model instance): parsed model
        inp (image): input image that model will predict on
        iou (numeric): intersection over union
        name (string): the name of the model (set arbitrarily)
    """
    print("model predicting...")
    ans = model.predict(inp)
    print("decoding bbox...")
    boxes = decode(ans[0], img_w, img_h, iou)
    img = (inp + 1) / 2
    img = img[0]
    for i in boxes:
        i = [int(x) for x in i]
        img = cv2.rectangle(
            img, (i[0], i[1]), (i[2], i[3]), color=(0, 255, 0), thickness=2
        )
        # plt.imshow(img)
        # plt.show()
        print("saving output...")
        cv2.imwrite(
            "./download/yolo-repo/test/result_" + str(name) + ".jpg", img * 255.0
        )


if __name__ == "__main__":
    import time

    start = time.process_time()
    model = load_model("./download/yolo-repo/model/text_detect_model.json")
    model.load_weights("./download/yolo-repo/model/text_detect.h5")
    import numpy as np

    for i in os.listdir("./download/yolo-repo/Test"):
        print("./download/yolo-repo/Test/" + str(i))
        img = cv2.imread("./download/yolo-repo/Test/" + str(i))
        img = cv2.resize(img, (512, 512))
        img = (img - 127.5) / 127.5
        predict_func(model, np.expand_dims(img, axis=0), 0.5, "sample")
    print("COMPLETED! runtime:", time.process_time() - start)


"""
1) Word Text detection
    - Text-Detection-using-Yolo-Algorithm-in-keras-tensorflow: https://github.com/Neerajj9/Text-Detection-using-Yolo-Algorithm-in-keras-tensorflow/blob/master/Yolo.ipynb
    - Slicing: https://github.com/obss/sahi/blob/main/demo/inference_for_yolov5.ipynb
2) Arranging bounding box: left-right, up-down
2) Textline detection
    - https://github.com/qurator-spk/sbb_textline_detection
4) Image to Latex
    - https://github.com/Green-Wood/CoMER/blob/master/example/example.ipynb
    - https://github.com/Emmarex/Mathematical-Handwriting-recognition
"""
