import os
import json

enterprise_path = os.getenv("SNMP_ENTERPRISE_HASH_TABLE")

from unit_tool.logger_unit import Logger
logger = Logger.debug_level()

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
        sec = int(sec[:-2])
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
    
    @staticmethod
    def determine_the_vendor_iana(sysObjectID:str)-> tuple:
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
    


