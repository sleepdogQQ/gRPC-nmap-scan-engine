FROM python:3.9-slim as base
FROM base as builder

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends vim git nmap

COPY ./ .

RUN python3 -m pip install -U pip
RUN python3 -m pip install -U setuptools
RUN pip install --no-cache-dir -r /requirements.txt

EXPOSE 50051