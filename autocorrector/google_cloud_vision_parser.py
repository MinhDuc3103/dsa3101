import os
from csv import Dialect

import cv2
import easyocr
import numpy as np
import pytesseract
from cv2 import threshold
from google.cloud import vision
from matplotlib.pyplot import contour, gray
from word_beam_search import WordBeamSearch

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_id.json"


def CloudVisionTextExtractor(handwritings):
    # convert image from numpy to bytes for submittion to Google Cloud Vision
    _, encoded_image = cv2.imencode(".png", handwritings)
    content = encoded_image.tobytes()
    image = vision.Image(content=content)

    # feed handwriting image segment to the Google Cloud Vision API
    client = vision.ImageAnnotatorClient()
    response = client.document_text_detection(image=image)

    return response


def getTextFromVisionResponse(response):
    texts = []
    for page in response.full_text_annotation.pages:
        for i, block in enumerate(page.blocks):
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = "".join([symbol.text for symbol in word.symbols])
                    texts.append(word_text)

    return " ".join(texts)


# handwritings = segments[2]

# Need to install tesseract-ocr and see the location of the .exe file
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'


def noise_removal(img):
    kernel = np.ones((1, 1), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)
    img = cv2.erode(img, kernel, iterations=1)
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
    img = cv2.medianBlur(img, 3)
    return img


def thin_font(img):
    img = cv2.bitwise_not(img)
    kernel = np.ones((2, 2), np.uint8)
    img = cv2.erode(img, kernel, iterations=1)
    img = cv2.bitwise_not(img)
    return img


def thick_font(img):
    img = cv2.bitwise_not(img)
    kernel = np.ones((2, 2), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)
    img = cv2.bitwise_not(img)
    return img


# Simple slicing box
for count in range(1):
    img = cv2.imread(f"modified-data/page{count}.jpg")
    hImg, wImg, _ = img.shape
    i = 0
    stepH = (int)(hImg / 5)
    stepW = (int)(wImg / 5)
    while i <= hImg:
        j = 0
        while j <= wImg:
            tem_img = img[i : i + stepH, j : j + stepW]
            cv2.imwrite(f"kernel_data/detected{i + j}.png", tem_img)
            gray_image = cv2.cvtColor(tem_img, cv2.COLOR_BGR2GRAY)
            thresh, im_bw = cv2.threshold(gray_image, 210, 220, cv2.THRESH_BINARY)
            no_noise = thin_font(im_bw)

            boxes = pytesseract.image_to_boxes(no_noise)
            for b in boxes.splitlines():
                b = b.split(" ")
                x, y, w, h = int(b[1]), int(b[2]), int(b[3]), int(b[4])
                cv2.rectangle(
                    img,
                    (x + j, stepH - y + i),
                    (w + j, stepH - h + i),
                    (50, 50, 255),
                    1,
                )
                cv2.putText(
                    img,
                    b[0],
                    (x + j, stepH - y + i + 13),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (50, 205, 50),
                    1,
                )
            j += stepW
        i += stepH

    cv2.imwrite(f"temp/detected{count}.png", img)
    print(count)

# reader = easyocr.Reader(['en'], gpu=True)
handwritings = cv2.imread("modified-data/page2.jpg")
responses = CloudVisionTextExtractor(handwritings)
handwrittenText = getTextFromVisionResponse(responses)
# --decoder wordbeamsearch
print(handwrittenText)


def autocorrector(handwrittenText):
    def apply_word_beam_search(mat, corpus, chars, word_chars):
        """Decode using word beam search. Result is tuple, first entry is label string, second entry is char string."""
        T, B, C = mat.shape

        # decode using the "Words" mode of word beam search with beam width set to 25 and add-k smoothing to 0.0
        assert len(chars) + 1 == C

        wbs = WordBeamSearch(
            25,
            "Words",
            0.0,
            corpus.encode("utf8"),
            chars.encode("utf8"),
            word_chars.encode("utf8"),
        )
        label_str = wbs.compute(mat)

        # result is string of labels terminated by blank
        char_str = []
        for curr_label_str in label_str:
            s = ""
            for label in curr_label_str:
                s += chars[label]  # map label to char
            char_str.append(s)
        return label_str[0], char_str[0]

    def load_mat(fn):
        """Load matrix from csv and apply softmax."""

        mat = np.genfromtxt(fn, delimiter=";")[:, :-1]  # load matrix from file
        T = mat.shape[0]  # dim0=t, dim1=c

        # apply softmax
        res = np.zeros(mat.shape)
        for t in range(T):
            y = mat[t, :]
            e = np.exp(y)
            s = np.sum(e)
            res[t, :] = e / s

        # expand to TxBxC
        return np.expand_dims(res, 1)

    # corpus = 'a ba'  # two words "a" and "ba", separated by whitespace
    # chars = 'ab '  # the characters that can be recognized (in this order)
    # word_chars = 'ab'  # characters that form words
    corpus = handwrittenText
    chars = """
            !"#&'()*+,-./0123456789:;?ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz 
            """
    word_chars = """ 
                'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "
                """

    # RNN output
    # 3 time-steps and 4 characters per time time ("a", "b", " ", CTC-blank)
    mat = np.array(
        [[[0.9, 0.1, 0.0, 0.0]], [[0.0, 0.0, 0.0, 1.0]], [[0.6, 0.4, 0.0, 0.0]]]
    )

    mat = load_mat("WordBeamSearch/data/bentham/mat_2.csv")
    res = apply_word_beam_search(mat, corpus, chars, word_chars)
    return res


res = autocorrector(handwrittenText)
print("")
print("Real example:")
print("Label string:", res[0])
print("Char string:", '"' + res[1] + '"')
