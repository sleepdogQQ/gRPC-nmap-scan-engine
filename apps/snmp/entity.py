import os
import json
import requests
from bs4 import BeautifulSoup
from typing import Sequence
from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, \
    ContextData, ObjectType, ObjectIdentity, getCmd, bulkCmd

from unit_tool.logger_unit import Logger
from apps.snmp.sysdescr import SysDescr
from apps.snmp.reference.constants import OID_DEVICEINFO, OID_SYSTEM

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
                    item = {}
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

class SNMPServerInfo():
    def __init__(self,snmp_deviceinfo_data_record:dict , raw_deviceinfo:dict, community_name:str, host:str):
        self.snmp_deviceinfo_data_record = snmp_deviceinfo_data_record
        self.raw_deviceinfo = raw_deviceinfo
        self.community_name = community_name
        self.host = host
    
    @classmethod
    def declare_from_data(cls, snmp_deviceinfo_data_record:dict={}, raw_deviceinfo:dict={}, community_name:str="", host:str=""):
        return cls(snmp_deviceinfo_data_record, raw_deviceinfo, community_name, host) 

    # 純秒數轉 datatime 格式 
    @staticmethod
    def second2time(sec: str) -> str:
        final_time = str()
        sec = int(sec)
        days = sec//86400
        hours = (sec % 86400)//3600
        minutes = ((sec % 86400) % 3600)//60
        seconds = ((sec % 86400) % 3600) % 60
        if (days):
            final_time += "{} days ".format(days)
        if (hours or days):
            final_time += "{} hours ".format(hours)
        if (minutes or hours or days):
            final_time += "{} minutes ".format(minutes)
        if (seconds or minutes or hours or days):
            final_time += "{} seconds".format(seconds)
        return final_time

    def expend_device_info(self) -> dict:
        # 初始化
        enterprise_path = os.getenv("SNMP_ENTERPRISE_HASH_TABLE")
        equipment_num = str()
        
        # 使用 sysObjectID 判斷屬於哪個 vendor
        def _determine_the_vendor_iana(sysObjectID:str)-> tuple:
            assert(isinstance(sysObjectID, str), f" sysObjectID must be str_type ")
            if("sysObjectID" == ""):
                logger("The sysObjectID field is empty, so we can,t to determine its equipment_num and vendor_iana")
                return ("", "")
            if("1.3.6.1.4.1." in sysObjectID):
                equipment_num = sysObjectID.split('1.3.6.1.4.1.')[1].split('.')[0] # 取到公司編號
            else:
                logger.info("The register_form is not finded, please run the enterprise_numbers.py first and check the env 「SNMP_ENTERPRISE_HASH_TABLE」 path")
                return ("", "")
            with open(enterprise_path, "r") as f:
                try:
                    register_form = json.load(f)
                except json.decoder.JSONDecodeError:
                    register_form = dict()
            if(equipment_num in register_form.keys()):
                vendor_iana = register_form.get(equipment_num)
                register_form.clear() # 釋放大量記憶體
                return (vendor_iana, equipment_num)
            else:
                logger.info("The sysObjectID data is can,t be parse")
                return ("", equipment_num)
        
        vendor_info_tuple =  _determine_the_vendor_iana(self.raw_deviceinfo.get("sysObjectID"))
        self.raw_deviceinfo.update({"vendor_iana":vendor_info_tuple[0]})
        equipment_num = vendor_info_tuple[1]

        # 加入 sysdescr 資訊
        def _add_sysdescr_info(device_info:dict , equipment_num:str)-> SysDescr:
            sysdescr = SysDescr.declare_from_data(
                raw_description = device_info.get("sysDescr"),
                equipment_num = equipment_num,
                vendor_iana = device_info.get("vendor_iana")
            )
            # 解析 sysDescr 欄位，並根據處理結果，宣告對應的 device_info 資訊
            if (not sysdescr.parse()):
                if (device_info.get('vendor_iana', False)):
                    # 若資料處理失敗，將無法解析的 sysDescr 自動化記下
                    sysdescr.create_new_unexcept_format()
            else:
                # 紀錄解析成功資料的配對詳情
                sysdescr.record_except_data()

            device_info.update({"vendor":sysdescr.vendor})
            device_info.update({"os":sysdescr.os})
            device_info.update({"model":sysdescr.model})
            device_info.update({"version":sysdescr.version})
            device_info.update({"monitor_type":sysdescr.monitor_type})
            device_info.update({"extra_detail":sysdescr.extra_detail})
            
            return device_info

        self.raw_deviceinfo = _add_sysdescr_info(self.raw_deviceinfo, equipment_num)

        # 轉換 SNMPServerInfo 中的 sysUpTime 時間顯示格式
        if (self.raw_deviceinfo.get("sysUpTime", False)):  # sysUpTime 如果是 None or 0
            time = SNMPServerInfo.second2time(self.raw_deviceinfo["sysUpTime"][:-2])
        else:
            time = "0 seconds"
        self.raw_deviceinfo["sysUpTime"] = time
        
        # 回傳最後結果
        return self.raw_deviceinfo

    @ staticmethod
    def replace_oid_description_2_text_description(detail:dict={}, updata_dynamic:bool=False) -> dict:
        """在找到 SNMP Server 與執行完 expend_device_info 的資料後，進行資料說明的轉換
        有可能會從既有資料替換也可以從網路上找

        Args:
            updata_dynamic (bool): 當為 True 時，將爬蟲找尋找不到紀錄的 oid 說明 
            detail (dict): oid 資料集

        Returns:
            dict: 轉換資料過後的 oid 資料集
        """
        # 先查 DB，找到則回傳
        # 沒找到， 再藉由 updata_dynamic 判斷是否要透過爬蟲爬取資料與更新資料集
        db_path = os.getenv("SNMP_OID_DESCRIPTION_VERNACULAR")

        def replace_from_db(db_path:str, oid: str) -> str:
            """
            根據 DB 替代資料
            """
            # 避免可能有此檔案但內容為空所導致的錯誤
            try:
                with open(db_path, "r") as f:
                    try:
                        oid_statistics = json.load(f)
                    except json.decoder.JSONDecodeError:
                        oid_statistics = dict()
            except:
                logger.info(" Can,t load the current db_data ")
                raise
            oid_list = (oid.split('.')[:-1])
            search_oid = '.'.join(oid_list)
            if (search_oid in oid_statistics):
                return oid.replace(search_oid, oid_statistics[search_oid])
            else:
                return False

        def replace_from_crawler(db_path:str, oid: str) -> str:
            """
            根據 crawler 替代資料
            """
            try:
                oid_list = (oid.split('.')[:-1])
                search_oid = '.'.join(oid_list)
                url = "http://oid-info.com/get/{}".format(search_oid)
                response = requests.get(url, timeout=10)
                if (response.status_code == 200):
                    soup = BeautifulSoup(response.text, "html.parser")
                    title = (soup.find("code").text)
                    # 避免可能有此檔案但內容為空所導致的錯誤
                    with open(db_path, 'r') as f:
                        try:
                            oid_statistics = json.load(f)
                        except json.decoder.JSONDecodeError:
                            oid_statistics = dict()
                    oid_statistics[search_oid] = title
                    with open(db_path, 'w') as f:
                        json.dump(oid_statistics, f)
                    return oid.replace(search_oid, title)
                else:
                    return False
            except requests.exceptions.ConnectTimeout:
                message = " 查詢網址回應過久，已自動斷開並回傳查詢失敗"
                logger.info(message)
                raise

        # 開始查詢並替代 detail 資料
        new_detail = dict()
        for each_oid in detail:
            db_res = replace_from_db(db_path, each_oid)
            if (db_res):  # 從資料庫中已有對應
                new_detail.update({db_res:detail.get(each_oid)})
            else:  # 資料庫無對應
                if (not updata_dynamic):  # 不做爬蟲
                    new_detail.update({each_oid:detail.get(each_oid)})
                else:
                    crawler_res = replace_from_crawler(db_path, each_oid)
                    if (crawler_res):
                        new_detail.update({crawler_res:detail.get(each_oid)})
                    else:  # 爬蟲依然沒結果
                        new_detail.update({each_oid:detail.get(each_oid)})
        return new_detail
        

