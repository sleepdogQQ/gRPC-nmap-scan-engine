from typing import Sequence
from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, \
    ContextData, ObjectType, ObjectIdentity, getCmd, bulkCmd
from apps.snmp.ori_snmp.reference.constants import OID_DEVICEINFO, OID_SYSTEM

from unit_tool.logger_unit import Logger
logger = Logger.debug_level()

snmp_version = {
        "v1": 0,
        "v2": 1
    }

class SNMPBaseHandler(object):

    def _init_host_config(self, host:str="", port:int=161):
        self.host = host
        self.port = port
    
    def _init_snmp_config(self, read_community:str="public", version:str="v2", convert_to_string:bool=False, 
                          max_repetitions:str="", oid:str=""):
        self.snmp_read_community = read_community
        self.snmp_version = version
        self.snmp_int_version = snmp_version.get(version, 1)
        self.snmp_convert_to_string = convert_to_string
        self.snmp_max_repetitions = max_repetitions
        self.snmp_oid = oid

    def __init__(self, host_config:dict, snmp_config:dict):
        self._init_host_config(**host_config)
        self._init_snmp_config(**snmp_config)

    @classmethod
    def declare_from_data(cls, build_data:dict):
        return cls(
            build_data.get("host_config",{}), 
            build_data.get("snmp_config",{})
        )

    # 使用 oid ，查詢設備基本資訊
    def get_deviceinfo(self):
        try:
            # 當執行 get_deviceinfo ，以下三值設為固定
            self.snmp_oid = OID_SYSTEM
            self.snmp_max_repetitions = 8
            self.snmp_convert_to_string = False

            data = self.get_bulk()
            if (data):
                # return data
                final_data = dict()
                for sys_info in OID_DEVICEINFO:
                    if (sys_info in data):
                        final_data[OID_DEVICEINFO[sys_info]] = data[sys_info]
                    else:
                        final_data[OID_DEVICEINFO[sys_info]] = ""
                return final_data
        except:
            logger.info(f"{self.host} snmp get_deviceinfo action happend something unexception fail ")
            raise

    # get 單一 oid 資訊
    def get(self) -> Sequence:
        ''' SNMP Get

            >>> client.get(0,'')
            ["Linux tc-fw 3.10.0-693cpx86_64 #1 SMP Thu Dec 23 15:16:23 IST 2021 x86_64"]
        '''
        try:
            # get 功能
            iterator = getCmd(
                SnmpEngine(),
                # 關聯表相關設定
                CommunityData(self.snmp_read_community,
                              mpModel=self.snmp_int_version),
                # 要抓取的 host ip 與 port
                UdpTransportTarget((self.host, self.port)),
                ContextData(),
                ObjectType(ObjectIdentity(self.snmp_oid))  # 所要查詢的 oid 代號
            )
            result = []

            error_indication, error_status, error_index, var_binds = next(
                iterator)

            # 若結果非正確
            if error_indication or error_status:
                logger.info(f"{self.host} snmp get data, but the data is error for snmp, so return the result current")
                return result

            for name, val in var_binds:
                if (str(val) != ''):
                    if (self.snmp_convert_to_string):
                        result.append(val.prettyPrint())
                    else:
                        result.append(str(val))
                else:
                    logger.info(f" {self.snmp_oid} get oid success, but there is no data")
                    return False
            return result
        except:
            logger.info(f"{self.host} snmp get action happend something unexception fail ")
            raise

    # get 的 bulk 形式，可取代 getnext ，給定 oid 後，抓取 max_repetitions 數量的oid結果
    def get_bulk(self) -> dict:
        try:
            '''
            SNMP getbulk request
            max_repetitions: This specifies the maximum number of iterations over the repeating variables.
            oid: oid
            '''
            # getbulk 功能
            iterator = bulkCmd(
                SnmpEngine(),
                CommunityData(self.snmp_read_community,
                              mpModel=self.snmp_int_version),
                UdpTransportTarget((self.host, self.port)),
                ContextData(), 1, 1,  # <-測試無影響結果，但不加入無法正常讀取 oid，故保留
                ObjectType(ObjectIdentity(self.snmp_oid)),
                maxRows=self.snmp_max_repetitions  # 所要得的結果數量（max_repetitions）
            )
            result = {}
            # 若結果非正確
            for error_indication, error_status, error_index, var_binds in iterator:
                if error_indication or error_status:
                    logger.info(f"{self.host}:{self.port}-Use [{self.snmp_read_community}] to get_bulk fail, so return the result current")
                    return result

                for name, val in var_binds:
                    if (self.snmp_convert_to_string):
                        if (str(val) == ''):
                            result.update({name.prettyPrint():''})
                        else:
                            result.update({name.prettyPrint():val.prettyPrint()})
                    else:
                        if (str(val) == ''):
                            result.update({str(name):''})
                        else:
                            result.update({str(name):str(val)})
            return result
        except:
            logger.info(f"{self.host} snmp get_bulk action happend something unexception fail ")
            raise
