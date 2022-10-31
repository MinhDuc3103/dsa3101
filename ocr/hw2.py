from csv import Dialect

import cv2
import easyocr
import pytesseract
from cv2 import threshold

reader = easyocr.Reader(["en"], gpu=False)
image = cv2.imread("modified-data/page2.jpg")
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
cv2.imwrite("gray_data/page2_gray.png", gray)

blur = cv2.GaussianBlur(gray, (7, 7), 0)
cv2.imwrite("blur_data/page2_blur.png", blur)

thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
cv2.imwrite("thresh_data/page2_thresh.png", thresh)

kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 13))
cv2.imwrite("kernel_data/page2_kernel.png", kernal)

width = image.shape[0]
blurred = cv2.blur(gray, (140, 20))
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (width, 1))
horizontal_mask = cv2.dilate(blurred, kernel, iterations=2)
horizontal_mask = cv2.bitwise_not(horizontal_mask)
horizontal_thresh = cv2.bitwise_and(img.copy(), img.copy(), mask=horizontal_mask)
cv2.imwrite("thresh_data/page2_horizontal_thresh.png", horizontal_thresh)

dilate = cv2.dilate(thresh, kernal, iterations=2)
cv2.imwrite("dilate_data/page2_dilate.png", kernal)

cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
horizontal_cnts = cv2.findContours(
    horizontal_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
)

cnts = cnts[0] if len(cnts) == 2 else cnts[1]
cnts = sorted(cnts, key=lambda x: cv2.boundingRect(x)[0])
for c in cnts:
    x, y, w, h = cv2.boundingRect(c)
    roi = image[y : y + h, x : x + w]
    result = reader.readtext(roi)
    cv2.imwrite("temp/page2_box.png", roi)
    cv2.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 2)
    if result:
        print(result[0][1])

cv2.imwrite("temp/page2.png", image)
