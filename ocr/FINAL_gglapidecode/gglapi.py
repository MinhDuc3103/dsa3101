import os

import cv2
from google.cloud import vision

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "dsa3101-2210-12-math-0c5fbe8196aa.json"


digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]


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
                    check = False
                    maxX = 0
                    maxY = 0
                    minX = 10000
                    minY = 10000
                    word_text = "".join([symbol.text for symbol in word.symbols])
                    for i in word_text:
                        if i in digits:
                            check = True
                    if check:
                        for symbol in word.symbols:
                            for i in symbol.bounding_box.vertices:
                                maxX = max(maxX, i.x)
                                minX = min(minX, i.x)
                                maxY = max(maxY, i.y)
                                minY = min(minY, i.y)
                        cv2.rectangle(
                            handwritings, (minX, minY), (maxX, maxY), (36, 255, 12), 2
                        )
                    texts.append(word_text)

    return " ".join(texts)


# reader = easyocr.Reader(['en'], gpu=True)
for page in range(60):
    handwritings = cv2.imread(f"modified-data/page{page}.jpg")
    responses = CloudVisionTextExtractor(handwritings)
    handwrittenText = getTextFromVisionResponse(responses)
    cv2.imwrite(f"temp/{page}.png", handwritings)
# print(responses)
