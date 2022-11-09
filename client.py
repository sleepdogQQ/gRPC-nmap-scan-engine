import logging
import grpc
import json
import scan_pb2, scan_pb2_grpc
from google.protobuf.json_format import MessageToDict

scan_condition = {
    "scan_mod":"default",
    "scan_host_range": "10.40.192.250-254",
    "scan_host_port": "1-1024",
    "scan_host_exclude": "",
    "scan_speed": "T3",
    "scan_delay": "0ms",
    "scan_host_timeout": "500ms",
    "scan_args": ""
}

def run():
    # with grpc.insecure_channel('server:50051') as channel:# docker
    with grpc.insecure_channel('127.0.0.1:50051') as channel:
        stub = scan_pb2_grpc.ScanServiceStub(channel)
        responses = stub.Scan(scan_pb2.ScanParameter(**scan_condition))
        for each_response in responses:
            result = MessageToDict(each_response)
            # print(type(result.get("status")))

if __name__ == '__main__':
    logging.basicConfig()
    run()


