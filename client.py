import os
import logging
import grpc
import json
import scan_pb2
import scan_pb2_grpc
from google.protobuf.json_format import MessageToDict
from google.protobuf.descriptor_pool import DescriptorPool
# from grpc_reflection.v1alpha.proto_reflection_descriptor_database import ProtoReflectionDescriptorDatabase

scan_condition = {
    "scan_mod": "default",
    "scan_host_range": "10.40.192.250-254",
    "scan_host_port": "1-1024",
    "scan_host_exclude": "",
    "scan_speed": "T3",
    "scan_delay": "0ms",
    "scan_host_timeout": "500ms",
    "scan_args": ""
}

# 先把 Token 寫在這，好理解
_ACCESS_TOKEN = "systex_token"


class AuthGateway(grpc.AuthMetadataPlugin):

    def __call__(self, context, callback):
        signature = context.method_name[::-1]
        callback(((_ACCESS_TOKEN, signature),), None)


def run():

    # create 自定義的 credentials
    call_credentials = grpc.metadata_call_credentials(
        AuthGateway(), name='auth gateway')

    CRT_PATH = os.path.join('.', 'server.crt')

    with open(CRT_PATH) as f:
        trusted_certs = f.read().encode()

    # create SSL credentials
    channel_credentials = grpc.ssl_channel_credentials(
        root_certificates=trusted_certs)

    # 組合成複合 credentials
    composite_credentials = grpc.composite_channel_credentials(
        channel_credentials,
        call_credentials,
    )

    try:
        with grpc.secure_channel('localhost:50051', composite_credentials) as channel:
            stub = scan_pb2_grpc.ScanServiceStub(channel)
            responses = stub.Scan(scan_pb2.ScanParameter(**scan_condition))
            for response in responses:
                print(response)
    except grpc.RpcError as rpc_error:
        # 這裡還可以根據 status code 細分例外處理，但暫時先統一寫 log
        # logger.error(
        #     f'Received RPC error: code={rpc_error.code()} message={rpc_error.details()} traceback= {traceback.print_exc()}')
        return 'error'

    # for response in responses:
    #     print(response)
    # with grpc.insecure_channel('server:50051') as channel:# docker
    # with grpc.insecure_channel('localhost:50051') as channel:

    #     # Reflection
    #     reflection_db = ProtoReflectionDescriptorDatabase(channel)
    #     services = reflection_db.get_services() # 取的所有有註冊的 services 服務
    #     print(services)

    #     # ! 官網範例，但無法在本機成功執行
    #     # + 無法更改原程式碼內容，暫不知如何偵錯
    #     # desc_pool = DescriptorPool(reflection_db)
    #     # server_desc = desc_pool.FindServiceByName('ScanServer')
    #     # print(server_desc)
    #     # method_desc =  server_desc.FindMethodByName("Scan")
    #     # print(method_desc)

    #     stub = scan_pb2_grpc.ScanServiceStub(channel)
    #     responses = stub.Scan(scan_pb2.ScanParameter(**scan_condition))
    #     for each_response in responses:
    #         result = MessageToDict(each_response)
    #         # print(type(result.get("status")))


if __name__ == '__main__':
    logging.basicConfig()
    run()
