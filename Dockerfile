FROM python:3.9-slim as base
FROM base as builder

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends vim git nmap make


RUN mkdir /grpc_server
WORKDIR /grpc_server
COPY ./ .

RUN python3 -m pip install -U pip
RUN python3 -m pip install -U setuptools
RUN pip install --no-cache-dir -r ./requirements.txt

RUN make generate_server_crt
# RUN openssl genrsa -out base_grpc/SSL/server.key 2048
# RUN openssl req -new -config ssl.conf -x509 -sha256 -key base_grpc/SSL/server.key -out base_grpc/SSL/server.crt -days 3650 
# RUN sh base_grpc/SSL/create.sh 

EXPOSE 50051