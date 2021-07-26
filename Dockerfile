FROM arm32v7/python:3 AS builder
RUN git clone -b release-3.22 -q --no-tags --single-branch https://gitlab.com/gpsd/gpsd.git /usr/src/app/
WORKDIR /usr/src/app/gps
RUN sed -e 's/\@GPSAPIVERMAJ\@/3/' -e 's/\@GPSAPIVERMIN\@/22/' __init__.py.in > __init__.py && sed -e 's/\@VERSION\@/3.22/' gps.py.in > gps.py

FROM arm32v7/python:3
WORKDIR /usr/src/app

RUN pip install --no-cache-dir RPi.GPIO tornado zmq influxdb-client
COPY --from=builder /usr/src/app/gps /usr/local/lib/python3.9/site-packages/gps

#COPY ./app ./ #not needed during development.
CMD [ "python3", "./main.py"]
