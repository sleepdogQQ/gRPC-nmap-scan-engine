import os
from apps.snmp.datadog_snmp.snmp import SnmpCheck
import yaml

data_folder = os.getenv("DATA_FOLDER")

from unit_tool.logger_unit import Logger
logger = Logger.debug_level()

class DeviceExDataHandler(object):
    """
    介於 Datadog Snmp 與 SNMPServerInfo 中間件
    """

    def _init_snmp_check(self):
        config = {
            'network_address': f"{self.snmp_deviceinfo_data_record.get('host_config', {}).get('host')}/32",
            'port': self.snmp_deviceinfo_data_record.get("host_config", {}).get("port"),
            'community_string': self.snmp_deviceinfo_data_record.get("snmp_config", {}).get("read_community"),
        }
        check = SnmpCheck('snmp', {}, [config])
        return check

    def __init__(self, snmp_deviceinfo_data_record:dict, sysobject_oid:str):
        self.sysobject_oid = sysobject_oid
        self.snmp_deviceinfo_data_record = snmp_deviceinfo_data_record
        self.check = self._init_snmp_check()

    @classmethod
    def declare_from_data(cls, snmp_deviceinfo_data_record:dict, sysobject_oid:str):
        return cls(
            snmp_deviceinfo_data_record=snmp_deviceinfo_data_record,
            sysobject_oid=sysobject_oid
        )

    def detect_device_info(self) -> dict:
        
        def _parsed_extends(root_yaml:str) -> list:
            ref_yaml_file = list() # total record
            extend_stack = list() # detect

            ref_yaml_file.append(root_yaml)
            extend_stack.append(root_yaml)

            while(len(extend_stack)):
                current_yaml =  extend_stack.pop() # Filename
                current_yaml = os.path.join(data_folder, current_yaml) # Add filepath
                with open(current_yaml, 'r') as f:
                    file_context = (yaml.safe_load(f))
                if("extends" not in file_context): # No yaml file need to be extended
                    continue
                for next_yaml_file in file_context.get("extends", []):
                    if(next_yaml_file not in ref_yaml_file):
                        ref_yaml_file.append(next_yaml_file)
                        extend_stack.append(next_yaml_file)
        
            return ref_yaml_file
        
        def _parsed_metadata(ref_yaml_file:list) -> list:
            ref_metadata = list()

            for i in ref_yaml_file:
                current_yaml = os.path.join(data_folder, i) # Add filepath
                with open(current_yaml, 'r') as f:
                    file_context = (yaml.safe_load(f))
                if('metadata' not in file_context):
                    continue
                ref_metadata.append(file_context.get("metadata", {}))

            return ref_metadata
        
        def _flat_device(device_data:dict) -> dict:
            temp_dict = dict()
            for i in device_data.get('fields'):
                if("value" in device_data.get('fields').get(i)):
                    temp_dict.update({i:device_data.get('fields').get(i).get("value")})
                if("symbol" in device_data.get('fields').get(i)):
                    temp_dict.update({i:device_data.get('fields').get(i).get("symbol")})
                if("symbols" in device_data.get('fields').get(i)):
                    temp_dict.update({i:device_data.get('fields').get(i).get("symbols")})
            return temp_dict

        profile = self.check._profile_for_sysobject_oid(self.sysobject_oid)
        all_ref_yml_file = _parsed_extends(f"{profile}.yaml")
        ref_metadata = _parsed_metadata(all_ref_yml_file)

        flat_data = dict()
        for data in ref_metadata:
            if("device" in data):
                flat_data.update(_flat_device(data.get("device")))
        
        return flat_data

    def expend_device_detail_info(self) -> dict:

        detail = dict()

        host_config = self.check._build_autodiscovery_config(self.check._config.instance, self.snmp_deviceinfo_data_record.get('host_config', {}).get('host'))
        profile = self.check._profile_for_sysobject_oid(self.sysobject_oid)
        host_config.refresh_with_profile(self.check.profiles[profile])
        host_config.add_profile_tag(profile)
        detail.update({"tags":host_config.tags})
        detail.update({"metrics":host_config.metrics})

        return detail

    def expend_device_interface_info(self):

        def _parsed_extends(root_yaml:str) -> list:
            ref_yaml_file = list() # total record
            extend_stack = list() # detect

            ref_yaml_file.append(root_yaml)
            extend_stack.append(root_yaml)

            while(len(extend_stack)):
                current_yaml =  extend_stack.pop() # Filename
                current_yaml = os.path.join(data_folder, current_yaml) # Add filepath
                with open(current_yaml, 'r') as f:
                    file_context = (yaml.safe_load(f))
                if("extends" not in file_context): # No yaml file need to be extended
                    continue
                for next_yaml_file in file_context.get("extends", []):
                    if(next_yaml_file not in ref_yaml_file):
                        ref_yaml_file.append(next_yaml_file)
                        extend_stack.append(next_yaml_file)
        
            return ref_yaml_file
        
        def _parsed_interface(ref_yaml_file:list) -> list:

            ref_interface = list()

            for i in ref_yaml_file:
                current_yaml = os.path.join(data_folder, i) # Add filepath
                with open(current_yaml, 'r') as f:
                    file_context = (yaml.safe_load(f))
                if('interface' not in file_context.get("metadata", {})):
                    continue
                ref_interface.append(file_context.get("metadata").get("interface", {}))

            return ref_interface

        profile = self.check._profile_for_sysobject_oid(self.sysobject_oid)
        all_ref_yml_file = _parsed_extends(f"{profile}.yaml")
        interface_data = _parsed_interface(all_ref_yml_file)
        
        return interface_data