# -*- coding: utf-8 -*-
# date: 2022/12/15
# author: yuchen
import warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
load_dotenv()
from base_grpc.proto_file import scan_pb2_grpc, scan_pb2
from typing import List
import grpc
import json
import os
import re
import sys
import requests
import traceback
from google.protobuf.json_format import MessageToDict
from grpc_reflection.v1alpha import reflection
from base_grpc.grpc_server import SSLgRPCServer
from apps.nmap_scan.nmmain import Scanner
from unit_tool.base_unit import record_program_process
from apps.rapid7_asset.middleware import Rapid7API, Rapid7Handler, UploadServer
from apps.snmp import DeviceExDataHandler
from apps.snmp.ori_snmp import SNMPBaseHandler, SNMPServerInfo
from apps.snmp.ori_snmp.reference.constants import BASE_DEVICEINFO_VALUE

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
        scanner = Scanner()
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
            message = " Base unexcption error happend"
            logger.info(message)
            logger.debug(sys.exc_info())
            logger.debug(traceback.format_exc())
            return scan_pb2.SNMPResponse(status=False, message=message, result=None)

    def Discover(self, request, context) -> scan_pb2.SNMPResponse:
        try:
            result = dict()

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
                        if(res.get("scan", {})=={}):
                            logger.info(f"{scanner.hosts} scan success, but not get any data")
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

            # 個別設備（ip, host）擴充 deviceinfo_set 資訊
            for index, SNMPServerInfObject in enumerate(snmp_server_info_set):
                device_info_data = dict()
                assert(isinstance(SNMPServerInfObject,SNMPServerInfo), " every (snmp_server_info_set) args must be SNMPServerInfo object")
                
                # 確定 sysObjectID 並非為空自串
                sysObjectID = SNMPServerInfObject.raw_deviceinfo.get("sysObjectID")
                if(sysObjectID == ''):
                    logger.info(f"{SNMPServerInfObject.host} get_deviceinfo success,but not get the sysObjectID, so skip the deviceinfo_expend")
                    continue

                #+ 前置階段（基本資料）
                # 紀錄 snmp 基本訊息
                device_info_data.update({"port":nmap_config.get("port")})
                device_info_data.update({"read_community":SNMPServerInfObject.community_name})
                device_info_data.update({"version":snmp_config.get("version")})
                
                #+ 第一階段（device_iana 資料）
                device_info_data.update({"base_device_info":dict()})
                vendor_info_tuple =  SNMPServerInfObject.determine_the_vendor_iana(sysObjectID)
                device_info_data.get("base_device_info", {}).update({"vendor_iana": vendor_info_tuple[0]})
                device_info_data.get("base_device_info", {}).update({"equipment_num": vendor_info_tuple[1]})
                
                # DeviceExDataHandler init
                discover_handler = DeviceExDataHandler.declare_from_data(SNMPServerInfObject.snmp_deviceinfo_data_record, sysObjectID)
                
                #+ 第一階段（device 資料）
                # 從 sysObjectID 判斷廠牌與延伸資料
                flat_data = discover_handler.detect_device_info()
                def _simple_snmp_get(snmp_scan_ref:dict, oid) -> str:
                    oid_result = str
                    get_data = {
                        "scan_type":"get",
                        "host_config":{
                            "host": snmp_scan_ref.get("host_config", {}).get("host"),
                            "port": snmp_scan_ref.get("host_config", {}).get("port")
                        },
                        "snmp_config":{
                            "read_community": snmp_scan_ref.get("snmp_config", {}).get("read_community"),
                            "version": snmp_scan_ref.get("snmp_config", {}).get("version"),
                            "oid": oid
                        }
                    }
                    snmp_handler = SNMPBaseHandler.declare_from_data(get_data)
                    oid_result = snmp_handler.get()
                    if(oid_result):
                        return oid_result[0]
                    else:
                        return "no result"
                temp = dict()
                for key, value in flat_data.items():
                    if(isinstance(value, str)):
                        temp.update({key: value})
                    elif(isinstance(value, list)):
                        for parsed_condition in value:
                            if("match_pattern" in parsed_condition): # 保留之後有可能會有其他標籤的可能
                                oid_result = _simple_snmp_get(SNMPServerInfObject.snmp_deviceinfo_data_record, parsed_condition.get("OID"))
                                regex_parse = re.compile(parsed_condition.get('match_pattern'))
                                parsed_res = regex_parse.match(oid_result)
                                if(parsed_res != None):
                                    temp.update({key: parsed_condition.get('match_value')})
                                    break
                                else:
                                    continue
                            temp.update({key: "regex not match"})
                    elif("extract_value" in value):
                        oid_result = _simple_snmp_get(SNMPServerInfObject.snmp_deviceinfo_data_record, value.get("OID"))
                        regex_parse = re.compile(value.get('extract_value'))
                        parsed_res = regex_parse.match(oid_result)
                        if(parsed_res != None):
                            temp.update({key: oid_result})
                        else:
                            temp.update({key: "regex not match"})
                    elif("OID" in value):
                        oid_result = _simple_snmp_get(SNMPServerInfObject.snmp_deviceinfo_data_record, value.get("OID"))
                        temp.update({key: oid_result})
                    
                    device_info_data.update({"extend_device_info":dict()})
                for value_name in temp:
                    if(value_name in BASE_DEVICEINFO_VALUE):
                        if(value_name == "sysUpTime" and temp.get(value_name) != 'no result'):
                            temp.update({value_name: SNMPServerInfObject.second2time(temp.get(value_name))})
                        device_info_data.get("base_device_info", {}).update({value_name: temp.get(value_name)})
                    else:
                        device_info_data.get("extend_device_info", {}).update({value_name: temp.get(value_name)})

                #+ 第二階段（metrics 資料）
                # 從 profile 的資料集延伸
                detail = discover_handler.expend_device_detail_info()
                device_info_data.update({"expand_device_detail_info":detail})

                #+ 第二階段（inteface 資料）
                interface = discover_handler.expend_device_interface_info()
                device_info_data.get("expand_device_detail_info", {}).update({"interface":interface})

                result.update({SNMPServerInfObject.host:device_info_data})
            
            return scan_pb2.SNMPResponse(status=True, message="success", result=json.dumps(result))
        except:
            message = " Discover unexception error happend"
            logger.info(message)
            logger.debug(sys.exc_info())
            logger.debug(traceback.format_exc())
            return scan_pb2.SNMPResponse(status=False, message=message, result=None)
class Rapid7Servicer(scan_pb2_grpc.Rapid7ServiceServicer):
    def Base(self, request, context) -> scan_pb2.Rapid7Response:
        try:
            logger.info(" --Rapid7_Base action begin--")
            data = MessageToDict(request, preserving_proto_field_name=True)
            # Server API 設定
            rapid7_api = Rapid7API()
            rapid7_api.setting_host_port(data.get("host"), data.get("port"))
            rapid7_api.setting_url(data.get("api_url"))
            rapid7_api.setting_auth(data.get("api_user"), data.get("api_password"))
            # Upload Server API 設定
            db_server = UploadServer()
            db_server.setting_host_port(os.getenv('DB_SERVER'), os.getenv('DB_PORT')) 
            db_server.setting_token(os.getenv("DB_TOKEN"))
            db_server.setting_headers()
            # 中間件 設定
            rapid7handler = Rapid7Handler()
            rapid7handler.setting_rapid7_api_source(rapid7_api)
            rapid7handler.setting_upload_api_source(db_server)
            # 核心邏輯
            site_info = rapid7handler.get_sites_detail(data.get("site_regex")) # 包含取得與過濾
            if(site_info == {}):
                message = "No any data need to be recorded"
                logger.info(message)
                return scan_pb2.Rapid7Response(status=True, message=message, result="")
            
            final_res = list()
            site_entity_set = rapid7handler.create_site_entity_set(site_info.get("resources", []))
            # asset detail
            for each_site in site_entity_set:
                asset_list = rapid7handler.get_assets_detail_and_create_asset_entity_set(each_site, page_size=data.get("asset_page_size", 10))
                each_site.add_belong_asset_data(asset_list)
            # asset vul detail
            for each_site in site_entity_set:
                try:
                    rapid7handler.get_rapid7_vul_report_info(each_site)
                except:
                    logger.info(f"{each_site.id} can,t create the vul report")
                    continue

            rapid7handler.upload_asset_info(each_site.belong_asset)
            rapid7handler.upload_asset_vul_info()
            
        except requests.exceptions.ReadTimeout:
            message = f"the requests action timed out, please check the server still works"
            logger.info(message)
            logger.debug(traceback.format_exc())
            return scan_pb2.Rapid7Response(status=False, message=message, result="")
        except json.decoder.JSONDecodeError as e:
            message = f'json parse fail'
            logger.info(message)
            logger.debug(traceback.format_exc())
            return scan_pb2.Rapid7Response(status=False, message=message, result="")
        except RuntimeError:
            message = "ckeck other exception message"
            logger.info(message)
            logger.debug(traceback.format_exc())
            return scan_pb2.Rapid7Response(status=False, message=message, result="")
        except:
            message = "unexpected"
            logger.info(message)
            logger.debug(sys.exc_info())
            logger.debug(traceback.format_exc())
            return scan_pb2.Rapid7Response(status=False, message=message, result="")
        else:
            return scan_pb2.Rapid7Response(status=True, message="Success", result=json.dumps(final_res))
        finally:
            logger.info(" --Rapid7_Base action end--")

class Server(SSLgRPCServer):
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
        scan_pb2_grpc.add_Rapid7ServiceServicer_to_server(
            Rapid7Servicer(), self._SERVER)
    
    def setting_reflection(self):
        SERVICE_NAMES = (
            reflection.SERVICE_NAME,
            scan_pb2.DESCRIPTOR.services_by_name['ScanService'].full_name,
            scan_pb2.DESCRIPTOR.services_by_name['SNMPService'].full_name,
            scan_pb2.DESCRIPTOR.services_by_name['Rapid7Service'].full_name
        )
        reflection.enable_server_reflection(SERVICE_NAMES, self._SERVER)
        
if __name__ == '__main__':
    setting_config = {
        "max_workers": 10, 
        "interceptors" : (SignatureValidationInterceptor(),)
    }
    try:
        server = Server("[::]", 50051)
        server.setting_base_config(setting_config)# 設定 grpc Server 通用基礎設定
        server.init_server_beforce_run() # 套用設定並建立 Server 實體物件
        # 需要先有實體才能設定的功能
        # --------------------------------
        server.register_service() # 註冊功能到實體上
        server.setting_reflection() # 在實體上開啟反射功能
        # --------------------------------
        record_program_process(logger, '...running...')
        server.run_with_ssl() # 啟動服務
    except TypeError:
        message = "check env is useful"
        record_program_process(logger, message)
        logger.debug(traceback.format_exc())
    except FileNotFoundError:
        message = "check file is exist"
        record_program_process(logger, message)
        logger.debug(traceback.format_exc())
    except KeyboardInterrupt:
        message = "...running stop..."
        record_program_process(logger, message)
        logger.debug(traceback.format_exc())
    except:
        message = "main unexceptional error"
        record_program_process(logger, message)
        logger.debug(sys.exc_info())
        logger.debug(traceback.format_exc())
        