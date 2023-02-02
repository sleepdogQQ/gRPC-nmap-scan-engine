from dotenv import load_dotenv
load_dotenv()
import traceback
import grpc
from base_grpc.proto_file import scan_pb2, scan_pb2_grpc
from google.protobuf.json_format import MessageToDict
from google.protobuf.descriptor_pool import DescriptorPool
from base_grpc.grpc_client import BasegRPClient
from unit_tool.logger_unit import Logger
from grpc_reflection.v1alpha.proto_reflection_descriptor_database import ProtoReflectionDescriptorDatabase
from unit_tool.base_unit import record_program_process

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
deviceinfo_data = {
    "scan_type":"deviceinfo",
    "host_config":{
        "host":"10.40.192.222",
        "port":161
    },
    "snmp_config":{
        "read_community":"public",
        "version":"v2"
    }
}
get_data = {
    "scan_type":"get",
    "host_config":{
        "host":"10.40.192.227",
        "port":161
    },
    "snmp_config":{
        "read_community":"public",
        "version":"v2",
        "oid":"1.3.6.1.4.1.2636.3.15.10.1.17"
        # "oid":"1.3.6.1.4.1.2620.1.6.123.1.49"
    }
}
getbulk_data = {
    "scan_type":"getbulk",
    "host_config":{
        "host":"10.40.192.227",
        "port":161,
    },
    "snmp_config":{
        "read_community":"public",
        "version":"v2",
        "max_repetitions":100,
        "convert_to_string":False,
        "oid":"1.3.6.1.4.1.2636.3.5.2.1.1"
        # "oid":"1.3.6.1.4.1.2620.1.6.123.1.49"
    }
}
scan_data = {
    # nmap
    "nmap_config":{
        "network":["10.40.192.222-227", "10.11.5.254", "10.11.5.249", "10.11.5.250"],
        # "network":["10.40.192.222-227"],
        # "network":["10.11.5.250"],
        "port":161,
        "scan_spend":"T3"
    },
    # snmp
    "snmp_config":{
        "read_community":["public", "systexadmin", "systex"],
        "version":"v2",
    },
    "update_dynamic":False
}
rapid7_data = {
    "host":"10.11.109.101",
    "port":3780,
    "api_url":"api/3",
    "api_user":"nxadmin",
    "api_password":"nxadmin",
    "site_regex":["^B85B[\w]?"]
}

logger = Logger.debug_level()

def run():
    client = BasegRPClient("grpc-on-52", 50051)
    try:
        with client.run() as channel:
            # Reflection
            reflection_db = ProtoReflectionDescriptorDatabase(channel)
            services = reflection_db.get_services() # 取的所有有註冊的 services 服務
            # print(services)
            # desc_pool = DescriptorPool(reflection_db)
            # print(desc_pool.FindServiceByName("Rapid7Service"))

            # stub = scan_pb2_grpc.ScanServiceStub(channel)
            # responses = stub.Scan(scan_pb2.ScanParameter(**scan_condition))
            # for response in responses:
            #     print(response)
            snmp_stub = scan_pb2_grpc.SNMPServiceStub(channel)
            # response = MessageToDict(snmp_stub.Base(scan_pb2.BaseRequest(**deviceinfo_data)))
            response = MessageToDict(snmp_stub.Discover(scan_pb2.DiscoverRequest(**scan_data)))
            # rapid7_stub = scan_pb2_grpc.Rapid7ServiceStub(channel)
            # response = MessageToDict(rapid7_stub.Base(scan_pb2.Rapid7Request(**rapid7_data)))
            print(response)
            return response
    except TypeError:
        message = "check env is useful"
        record_program_process(logger, message)
    except FileNotFoundError:
        message = "check file is exist"
        record_program_process(logger, message)
    except grpc.RpcError as rpc_error:
        # 這裡還可以根據 status code 細分例外處理，但暫時先統一寫 log
        logger.debug(
            f'Received RPC error: code={rpc_error.code()} message={rpc_error.details()} traceback= {traceback.print_exc()}')
        return None

if __name__ == '__main__':
    run()

