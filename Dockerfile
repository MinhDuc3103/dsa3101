FROM python

RUN apt-get update && apt-get install -y poppler-utils
RUN apt-get install -y libgl1-mesa-glx
RUN mkdir /app
COPY /app /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD python3 app.py

#docker build . -t haha
#docker run --name mathProj -d -p 80:80 haha  