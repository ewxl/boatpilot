FROM arm32v7/python:3
ENV DEBIAN_FRONTEND noninteractive

WORKDIR /usr/src/app

RUN apt update && apt install gpsd -y

RUN pip install --no-cache-dir RPi gps zmq tornado

COPY ./app ./
CMD [ "python", "./main.py" ]
