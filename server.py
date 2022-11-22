# -*- coding: utf-8 -*-
# date: 2022/10/31
# author: yuchen
import scan_pb2_grpc, scan_pb2, nmmain
from concurrent import futures
import logging
import grpc
import json
from google.protobuf.json_format import MessageToDict
import os
from grpc_reflection.v1alpha import reflection


KEY_PATH = os.path.join(os.path.split(__file__)[0], 'server.key')
CRT_PATH = os.path.join(os.path.split(__file__)[0], 'server.crt')



class ScanServicer(scan_pb2_grpc.ScanServiceServicer):

    def Scan(self, request, context):
        scanner = nmmain.Scanner()
        # + MessageToDict 和 MessageToJson 需要加上 preserving_proto_field_name=True，不然會自動將格式轉譯成小駝峰式
        result = scanner.nmap_scan(condition=MessageToDict(request, preserving_proto_field_name=True))
        for each_result in result.get("scan_result", []):
            for host, result in each_result.items():
                yield scan_pb2.ScanResult(ip=host, scan_result=json.dumps(result))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    scan_pb2_grpc.add_ScanServiceServicer_to_server(ScanServicer(), server)


    # Reflection
    SERVICE_NAMES = (
        reflection.SERVICE_NAME,
        scan_pb2.DESCRIPTOR.services_by_name['ScanService'].full_name,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    # 本來下面這句是打開，會導致不需要憑證就可以成功接至50051port
    # server.add_insecure_port('0.0.0.0:50051')  # docker


    # server.add_insecure_port('127.0.0.1:50051')

    # SSL/TLS
    try:
        with open(KEY_PATH) as f:
            private_key = f.read().encode()
        with open(CRT_PATH) as f:
            certificate_chain = f.read().encode()
    except FileNotFoundError:
        print("private_key or certificate_chain not found")
        return

    server_creds = grpc.ssl_server_credentials(((private_key, certificate_chain,),))
    server.add_secure_port('0.0.0.0:50051', server_creds)

    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
