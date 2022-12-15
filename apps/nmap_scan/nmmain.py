# -*- coding: utf-8 -*-
# date: 2022/10/12
# author: 鄭羽辰

import sys
import nmap
from datetime import datetime
from typing import Dict
import traceback
import platform
from unit_tool import Logger

logger = Logger.debug_level()

class Scanner:
    def __init__(self):
        self.hosts = str()
        self.args = str()
        self.condition = dict()

    def _every_values_is_str(self, data: dict) -> bool:
        assert isinstance(data, dict), "請確定傳入為字典（dict）格式"
        for keys in data:
            assert isinstance(data[keys], str), "每個參數都必須是 string 型態"
        return True

    def check_and_init_by_condition(self, condition: dict):
        self._every_values_is_str(condition)
        self.condition = condition
        self.hosts = condition.get("scan_host_range", "127.0.0.1")

    def setting_important_args(self):
        """
        根據 scan_mod 決定此次掃描要做的主要功能
        """
        scan_mode = self.condition.get('scan_mod', 'default')
        if scan_mode == 'custom':
            self.args = ' '.join(
                [self.args, self.condition.get('scan_args', '')])
        elif scan_mode == 'default':
            self.args = ' '.join([self.args, "-A"])
        elif scan_mode == 'host_discover':
            self.args = ' '.join([self.args, "-sn -n"])
        else:  # like default
            self.args = ' '.join([self.args, "-A"])

    def setting_additional_args(self):
        """
        額外其他條件，但並非所有，僅有較常用的
        包含：埠號指定、掃瞄速度、欲排除主機、掃描最多等待時間、掃描間隔
        """
        if (self.condition.get('scan_host_port', '')) != '':
            self.args = ' '.join(
                [self.args, f"-p {self.condition.get('scan_host_port')}"])
        if (self.condition.get('scan_speed', '')) != '':
            self.args = ' '.join(
                [self.args, f"-{self.condition.get('scan_speed')}"])
        if (self.condition.get('scan_host_exclude', '')) != '':
            self.args = ' '.join(
                [self.args, f"--exclude {self.condition.get('scan_host_exclude')}"])
        if (self.condition.get('scan_host_timeout', '')) != '':
            self.args = ' '.join(
                [self.args, f"--host-timeout {self.condition.get('scan_host_timeout')}"])
        if (self.condition.get('scan_delay', '')) != '':
            self.args = ' '.join(
                [self.args, f"--scan-delay {self.condition.get('scan_delay')}"])

    def scan(self) -> dict:
        try:
            assert self.hosts != "", "請先確定 scan host 範圍已指定"
            nm = nmap.PortScanner()
            logger.info(' :'.join([self.hosts, self.args]))
            logger.info("start time:" +
                        datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
            if platform.system() == 'Darwin':
                # handle macos should use sudo permission to do scan.
                result = nm.scan(hosts=self.hosts,
                                 arguments=self.args, sudo=True)
            else:
                # 'Linux' or others
                result = nm.scan(hosts=self.hosts, arguments=self.args)
            logger.info("end   time:" +
                        datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
            # 輸出結果
            return result
        except:
            logger.info(" scan 發生預期外錯誤，已回傳空字典")
            logger.debug(sys.exc_info())
            logger.debug(traceback.format_exc(1))
            return {}

    def final_result_handler(self, result: dict) -> dict:
        assert isinstance(result, dict)
        data = {}
        if result == {}:
            data.update({"scan_result": list()})
        elif "error" in ((result["nmap"])['scaninfo']):
            for i in ((result["nmap"])['scaninfo'])["error"]:
                logger.error(f'nmap scan occur error:\n{i.strip()}')
            data.update({"scan_result": list()})
        else:
            data.update({"scan_result": list()})
            for k, v in result.get('scan', {}).items():
                # 'tcp', 'udp' all key convert from int to str
                if 'tcp' in v:
                    old_tcp = v.pop('tcp')
                    v['tcp'] = {}
                    for port0, info in old_tcp.items():
                        v['tcp'][str(port0)] = info
                if 'udp' in v:
                    old_udp = v.pop('udp')
                    v['udp'] = {}
                    for port0, info in old_udp.items():
                        v['udp'][str(port0)] = info
                data["scan_result"].append({k: v})
        return data

    def nmap_scan(self, condition: Dict[str, str]) -> dict:
        # 確定參數型態正確
        self.check_and_init_by_condition(condition)
        # 加入重要參數
        self.setting_important_args()
        # 加入附屬參數
        self.setting_additional_args()
        # 開始掃描
        result = self.scan()
        # 整理並回傳結果
        data = self.final_result_handler(result)
        return data
