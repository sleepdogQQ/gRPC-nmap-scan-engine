import re
import os
import json
from unit_tool.logger_unit import Logger
from datetime import datetime
logger = Logger.debug_level()

UNKNOWN = 'UNKNOWN'

class SysDescr(object):
    def __init__(self, raw_description: str, equipment_num: str, vendor_iana:str) -> None:
        self.raw_description = raw_description
        self.equipment_num = equipment_num
        self.vendor_iana = vendor_iana
        self.vendor = UNKNOWN
        self.model = UNKNOWN
        self.os = UNKNOWN
        self.version = UNKNOWN
        self.monitor_type = UNKNOWN
        self.synax_detail = None
        self.extra_detail = list()
        self.success_parse_synax = list()
    
    @classmethod
    def declare_from_data(cls, raw_description:str="", equipment_num:str="", vendor_iana:str=None):
        return cls(raw_description, equipment_num, vendor_iana)

    def parse(self):
        """
        根據給予的 description 自動化判斷廠牌、系統等資訊
        """
        # 先檢查是否有相關廠牌可以查找
        try:
            if (not self.check_sys_company()):
                return False
        except:
            message = " 判斷所屬廠牌過程錯誤"
            logger.info(message)
            raise
        # 在檢查是否有此廠牌相關的詳細資料，可以更加完整的判斷這個設備的資料
        try:
            if (not self.discriminate_sysinfo()):
                message = (f" {self.raw_description} 無此系統格式資料，故無法解析系統格式")
                logger.info(message)
                return False
        except:
            message = (" 判斷系統詳情過程錯誤")
            logger.info(message)
            raise
        # 判斷成功
        return True

    def discriminate_sysinfo(self) -> bool:
        """
        嘗試解析切割出 sysDescr 中的設備資訊
        """
        try:
            def discriminate_deep_info(data: dict):
                # +本來有 check_type 用 oid 的加入方法，但這樣會讓 snmp 結構變得混亂，且可以用 extra_detail 去帶出其資訊，在確定有需求前，先移除此功能
                if (data['check_type'] == "str"):
                    return data['check_synax']
                if (data['check_type'] == "regex"):
                    return int(data['check_synax'])
                return UNKNOWN

            # 在這個廠牌下，多個設備各自可能的 parse 規則
            for every_detect in self.synax_detail:
                # 正則判斷法
                if (every_detect["check_type"] == "regex"):
                    for synax in every_detect['check_synax']:
                        parse = re.compile(r"{}".format(synax))
                        parse_res = parse.search(self.raw_description.strip())
                        # 要每一個 check_synax 都成功，否則失敗
                        if (not parse_res):
                            break
                    # check_synax 全部通過後，根據最後一個正則切割結果來給值
                    if (parse_res):
                        # 成功配對的 regex 列表
                        self.success_parse_synax = every_detect['check_synax']
                        # 額外擴充資訊
                        self.extra_detail = every_detect['extra_detail']
                        # 正式資訊統整
                        self.os = every_detect['os'] if (isinstance(
                            every_detect['os'], str)) else parse_res.group(every_detect['os'])
                        res = discriminate_deep_info(every_detect['model'])
                        self.model = res if (isinstance(
                            res, str)) else parse_res.group(res)
                        res = discriminate_deep_info(every_detect['version'])
                        self.version = res if (isinstance(
                            res, str)) else parse_res.group(res)
                        res = discriminate_deep_info(
                            every_detect['monitor_type'])
                        self.monitor_type = res if (isinstance(
                            res, str)) else parse_res.group(res)
                        return True
                    else:
                        continue
            # 最終還是沒有配對到任何一個成功
            return False

        except:
            message = (" discriminate_sysinfo 函式發生錯誤")
            logger.debug(message)
            raise

    def check_sys_company(self):
        """由 sysDescr 開頭判斷為哪一家廠牌，並回傳更詳細的鑑驗證則與參數

        Returns:
            bool: 是否有成功 parse
        """
        try:
            if (self.equipment_num == None):
                return False
            with open(os.getenv("SNMP_COMPANY_PARSE"), 'r') as f:
                try:
                    company_dict = json.load(f)
                except json.decoder.JSONDecodeError:
                    company_dict = dict()
                    
            # 尋找描述所對應的廠牌名稱
            if (self.equipment_num in company_dict):
                # 根據 check_synax 的數量，重新排序，讓較嚴苛的條件先進行比較
                def sort_check_synax(data):
                    """
                    回傳 check_synax 的數量
                    """
                    return len(data['check_synax'])
                sort_synax_detail = list(
                    company_dict.get(self.equipment_num, {}).get('synax_detail'))
                sort_synax_detail.sort(reverse=True, key=sort_check_synax)
                # 帶入結果
                self.vendor = company_dict[self.equipment_num]['vendor']
                self.synax_detail = sort_synax_detail
                return True
            else:
                self.vendor = self.vendor_iana
                self.synax_detail = None
                return False
        except:
            message = (" check_sys_company 函式發生錯誤")
            logger.info(message)
            raise

    def create_new_unexcept_format(self):
        try:
            check_synax_format = {
                'check_synax': [],
                'check_type': 'regex',
                'os': 'example',
                'model': {'check_synax': "example", 'check_type': 'str'},
                'monitor_type': {'check_synax': 'example', 'check_type': 'str'},
                'version': {'check_synax': 'example', 'check_type': 'str'},
                'extra_detail': []
            }

            file_path = os.getenv("SNMP_COMPANY_PARSE")
            regex_reserve_char = ['[', ']', '(', ')', '^']
            for char in regex_reserve_char:
                self.raw_description = self.raw_description.replace(
                    char, '\{}'.format(char))
            with open(file_path, 'r') as f:
                try:
                    record_res = json.load(f)
                except json.decoder.JSONDecodeError:
                    record_res = dict()
            # 如果 record_res 並沒有 關於此公司的任何紀錄，新增它的欄位
            if (self.equipment_num not in record_res):
                record_res[self.equipment_num] = dict()
                record_res.get(self.equipment_num, {}).update({"vendor":self.vendor_iana})
            # 紀錄範例並寫檔
            check_synax_format.get("check_synax", []).append(self.raw_description.strip())
            if(not record_res.get(self.equipment_num, {}).get("synax_detail",False)):
                record_res[self.equipment_num]["synax_detail"] = list() 
            record_res.get(self.equipment_num, {}).get("synax_detail",[]).append(check_synax_format) 
            with open(file_path, 'w')as f:
                json.dump(record_res, f)
            # 回傳成功
            return True
        except:
            message = " {} create_new_unexcept_format 紀錄失敗".format(
                self.raw_description)
            logger.info(message)
            raise

    def record_except_data(self):
        try:
            record_format = {
                "equipment_num": self.equipment_num,
                "vendor": self.vendor,
                "sysdescr": self.raw_description,
                "match_regex_list": self.success_parse_synax,
                "record_time": datetime.today().strftime("%Y-%m-%d, %H:%M")
            }

            file_path = os.getenv("SNMP_COMPANY_PARSE_SUCCESS_DATA")
            with open(file_path, 'r') as f:
                try:
                    res = json.load(f)
                except json.decoder.JSONDecodeError:
                    res = list()
            # 限制檔案大小機制
            if (len(res) > 1000):
                res = res[750:]
                message = "已儲存記錄超過1000筆資料，刷新資料以確保檔案不會過大"
                logger.info(message)

            res.append(record_format)
            with open(file_path, 'w') as f:
                json.dump(res, f)
            # 回傳成功
            return True
        except:
            message = " {} record_except_data 紀錄失敗".format(self.raw_description)
            logger.info(message)
            raise
