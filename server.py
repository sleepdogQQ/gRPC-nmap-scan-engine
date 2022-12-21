# -*- coding: utf-8 -*-
# date: 2022/12/15
# author: yuchen
from dotenv import load_dotenv
load_dotenv()
from base_grpc.proto_file import scan_pb2_grpc, scan_pb2
from typing import List
import grpc
import json
import os
import sys
import traceback
from pysnmp.smi.error import NoSuchObjectError
from google.protobuf.json_format import MessageToDict
from grpc_reflection.v1alpha import reflection
from base_grpc.grpc_server import SSLgRPCServer, BasegRPCServer
from apps.snmp.entity import SNMPBaseHandler, SNMPServerInfo
from apps.nmap_scan.nmmain import Scanner

from  unit_tool.logger_unit import Logger
logger = Logger.debug_level()
# 先把 Token 寫在這，好理解
_ACCESS_TOKEN = "systex_token"

class SignatureValidationInterceptor(grpc.ServerInterceptor):

    def __init__(self):

        def abort(ignored_request, context):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Invalid signature')

        self._abortion = grpc.unary_unary_rpc_method_handler(abort)

    def intercept_service(self, continuation, handler_call_details):

        method_name = handler_call_details.method.split('/')[-1]

        expected_metadata = (_ACCESS_TOKEN, method_name[::-1])

        if expected_metadata in handler_call_details.invocation_metadata:
            return continuation(handler_call_details)
        else:
            return self._abortion

class ScanServicer(scan_pb2_grpc.ScanServiceServicer):

    def Scan(self, request, context):
        scanner = nmmain.Scanner()
        # + MessageToDict 和 MessageToJson 需要加上 preserving_proto_field_name=True，不然會自動將格式轉譯成小駝峰式
        result = scanner.nmap_scan(condition=MessageToDict(
            request, preserving_proto_field_name=True))
        for each_result in result.get("scan_result", []):
            for host, result in each_result.items():
                yield scan_pb2.ScanResult(ip=host, scan_result=json.dumps(result))

class SnmpServicer(scan_pb2_grpc.SNMPServiceServicer):
    def Base(self, request, context) -> scan_pb2.SNMPResponse:
        try:
            data = MessageToDict(request, preserving_proto_field_name=True)
            snmp_action =  data.get("scan_type", None)
            snmp_handler = SNMPBaseHandler.declare_from_data(data)
            result = None

            if(snmp_action == "deviceinfo"):
                result = snmp_handler.get_deviceinfo()
            elif(snmp_action == "get"):
                result = snmp_handler.get()
            elif(snmp_action == "getbulk"):
                result = snmp_handler.get_bulk()
            else:
                logger.info("input request body is not right")            

            if result:
                return scan_pb2.SNMPResponse(status=True, message="success.", result=json.dumps(result))
            else:
                return scan_pb2.SNMPResponse(status=True, message="result is empty.", result=None)
        except:
            message = " unexcption error happend"
            logger.info(message)
            logger.debug(sys.exc_info())
            logger.debug(traceback.format_exc())
            return scan_pb2.SNMPResponse(status=False, message=message, result=None)

    def Discover(self, request, context) -> scan_pb2.SNMPResponse:
        try:
            data = MessageToDict(request, preserving_proto_field_name=True)

            nmap_config = data.get("nmap_config", {})
            snmp_config = data.get("snmp_config", {})

            # 用 nmap 找到疑似有開啟 snmp 的 server
            def _discover_hosts() -> list:
                """用 nmap 掃描，並將疑似有開啟的主機列舉紀錄後回傳

                Returns: 
                    list: host 列舉紀錄
                """
                scanner = Scanner()
                detected_open_host = list()
                scan_spend = ''.join(['-', nmap_config.get("scan_spend", "T3")])
                scan_range = nmap_config.get("network", [])
                scan_port = str(nmap_config.get("port", 161))
                scan_args = f"-sU --open {scan_spend} -p {scan_port}"# 用 udp 協定掃描有開啟指定埠號的主機
                for network in scan_range:
                    scanner.hosts = network
                    scanner.args = scan_args
                    try:
                        res = scanner.scan()
                        detected_open_host.extend(list(res.get("scan",{}).keys()))
                    except:
                        logger.info(f"discover {network} failed")
                        raise
                return detected_open_host

            detected_open_host = _discover_hosts()
            
            # 依據 read_community 測試能否抓取到 host snmp deviceinfo 資料
            def _test_and_record_deviceinfo(detected_open_host:list) -> List[SNMPServerInfo]:
                """將抓到的 host 使用 read_community 測試是否可以生成 SNMPServerInfo 資料

                Args:
                    detected_open_host (list): host 紀錄

                Returns:
                    List[SNMPServerInfo]: SNMPServerInfo 實體集合
                """
                snmp_server_info_set = list()
                for community_name in snmp_config.get('read_community', list()):
                    changed_list = detected_open_host.copy()
                    for index, each_host in enumerate(changed_list):
                        deviceinfo_data = {
                            "scan_type":"deviceinfo",
                            "host_config":{
                                "host":each_host,
                                "port":nmap_config.get("port", 161),
                            },
                            "snmp_config":{
                                "read_community":community_name,
                                "version":snmp_config.get("version", "v2"),
                            }
                        }
                        snmp_handler = SNMPBaseHandler.declare_from_data(deviceinfo_data)
                        raw_deviceinfo = snmp_handler.get_deviceinfo()
                        if(raw_deviceinfo): # 有抓到資料，刪除 host 紀錄加速查詢，並建立 SNMPServerInfo 物件
                            detected_open_host.pop(detected_open_host.index(each_host)) # 不影響本此循環，下一個 community_name 時生效
                            snmp_server_info_set.append(SNMPServerInfo.declare_from_data(
                                snmp_deviceinfo_data_record = deviceinfo_data,
                                raw_deviceinfo=raw_deviceinfo,
                                community_name=community_name,
                                host=each_host)
                            )
                            
                return snmp_server_info_set

            snmp_server_info_set = _test_and_record_deviceinfo(detected_open_host)

            result = dict()
            # 擴充 deviceinfo_set 資訊
            for index, SNMPServerInfObject in enumerate(snmp_server_info_set):
                assert(isinstance(SNMPServerInfObject,SNMPServerInfo), " every (snmp_server_info_set) args must be SNMPServerInfo object")
                # 從 sysObjectID  判斷廠牌與 vendor_iana 等資訊
                device_info_data = SNMPServerInfObject.expend_device_info()
                # 先紀錄必要資訊
                device_info_data.update({"port":nmap_config.get("port")})
                device_info_data.update({"read_community":SNMPServerInfObject.community_name})
                device_info_data.update({"version":snmp_config.get("version")})
                # 根據 sysObjectID 使用 get_bulk 抓取資料
                device_info_data.update({"detail":dict()}) # 先宣告儲存空間
                def _get_more_info_by_sysobjectid(host:str, device_info_data:dict) -> dict:
                    getbulk_data = {
                        "scan_type":"getbulk",
                        "host_config":{
                            "host":host,
                            "port":device_info_data.get("port"),
                        },
                        "snmp_config":{
                            "read_community":device_info_data.get("read_community"),
                            "version":device_info_data.get("version"),
                            "max_repetitions":1000,
                            "convert_to_string":False,
                            "oid":device_info_data.get("sysObjectID")
                        }
                    }
                    try:
                        snmp_handler = SNMPBaseHandler.declare_from_data(getbulk_data)
                        return snmp_handler.get_bulk()
                    except NoSuchObjectError as e:
                        message = f" Can,t use the oid({device_info_data.get('sysObjectID')}) to get_bulk in host({host}), please check it is correct"
                        logger.info(message)
                        raise
                try:
                    more_detail_oid_info = _get_more_info_by_sysobjectid(SNMPServerInfObject.host, device_info_data)
                except NoSuchObjectError as e:
                    message = f" {SNMPServerInfObject.host} run get_more_info_by_sysobjectid fun was fail"
                    logger.info(message)
                    continue
                
                # 將前一動得到的 more_detail_oid_info 結果轉換成可讀性較高的英文文字敘述再寫入
                def _convert_oid_description(more_detail_oid_info:dict) -> dict:
                    more_detail_oid_info = SNMPServerInfo.replace_oid_description_2_text_description(
                        more_detail_oid_info, 
                        updata_dynamic = data.get("update_dynamic", False)
                    )
                    if(more_detail_oid_info):
                        return more_detail_oid_info
                    else:
                        message = f" [ip:{SNMPServerInfObject.host}-convert_oid_description, oid:{device_info_data.get('sysObjectID', '')}] can,t find any other data"
                        logger.info(message)
                        return {}
                device_info_data.get("detail", {}).update({"by_sys_objectID":_convert_oid_description(more_detail_oid_info)})

                # 從 extra_detail 擴充 device_info資訊
                def _get_more_info_by_extra_detail(device_info_data:dict, snmp_reference:dict) -> dict:
                    extra_detail_res = dict()
                    if(device_info_data.get("extra_detail", False)):
                        for every_oid in device_info_data.get('extra_detail', list()):
                            get_data = {
                                "scan_type":"get",
                                "host_config":{
                                    "host":snmp_reference.get("host_config",{}).get("host"),
                                    "port":snmp_reference.get("host_config",{}).get("port")
                                },
                                "snmp_config":{
                                    "read_community":snmp_reference.get("snmp_config",{}).get("read_community"),
                                    "version":snmp_reference.get("snmp_config",{}).get("version"),
                                    "oid":every_oid
                                }
                            }
                            snmp_hander = SNMPBaseHandler.declare_from_data(get_data)
                            extra_res = snmp_hander.get()
                            if (extra_res):
                                extra_detail_res.update({every_oid:extra_res[0]})
                    return extra_detail_res
                device_info_data.get("detail", {}).update({"by_extra_oid":_get_more_info_by_extra_detail(device_info_data, SNMPServerInfObject.snmp_deviceinfo_data_record)})
                device_info_data.pop("extra_detail")
                # 把資訊與對應主機補上
                result.update({SNMPServerInfObject.host:device_info_data})
            
            return scan_pb2.SNMPResponse(status=True, message="success", result=json.dumps(result))
        except:
            message = " unexception error happend"
            logger.info(message)
            logger.debug(sys.exc_info())
            logger.debug(traceback.format_exc())
            return scan_pb2.SNMPResponse(status=False, message=message, result=None)

class Server(BasegRPCServer):
    KEY_PATH = os.getenv("GRPC_KEY_PATH")
    CRT_PATH = os.getenv("GRPC_CRT_PATH")

    def __init__(self, host:str, port:int):
        super().__init__(host, port)
        self.setting_base_config(setting_config)

    def register_service(self):
        scan_pb2_grpc.add_ScanServiceServicer_to_server(
            ScanServicer(), self._SERVER)
        scan_pb2_grpc.add_SNMPServiceServicer_to_server(
            SnmpServicer(), self._SERVER)
    
    def setting_reflection(self):
        SERVICE_NAMES = (
            reflection.SERVICE_NAME,
            scan_pb2.DESCRIPTOR.services_by_name['ScanService'].full_name,
            scan_pb2.DESCRIPTOR.services_by_name['SNMPService'].full_name,
        )
        reflection.enable_server_reflection(SERVICE_NAMES, self._SERVER)
        
if __name__ == '__main__':
    logger.info("--begin--")
    setting_config = {
        "max_workers": 10, 
        "interceptors" : (SignatureValidationInterceptor(),)
    }

    server = Server("grpc-on-206", 50051)
    server.setting_base_config(setting_config)# 設定 grpc Server 通用基礎設定
    server.init_server_beforce_run() # 套用設定並建立 Server 實體物件
    # 需要先有實體才能設定的功能
    # --------------------------------
    server.register_service() # 註冊功能到實體上
    server.setting_reflection() # 在實體上開啟反射功能
    # --------------------------------
    server.run() # 啟動服務

