import json
import re
import os
from typing import List

from apps.rapid7_asset.data_entity import Asset, Site
from unit_tool.logger_unit import Logger
from apps.rapid7_asset.server import Rapid7API
logger = Logger.debug_level()

class Rapid7Handler():
    """
    作為 Rapid7 服務器 與 Rapid7 資料處理 的中間件
    """
    def  __init__(self) -> None:
        self.rapid7_api = Rapid7API

    def setting_rapid7_api_source(self, rapid7_api):
        self.rapid7_api = rapid7_api
    
    def __check_the_site_name_by_regex(self, data:dict, site_regex:list) -> dict:
        if(not isinstance(site_regex, list) or site_regex == []):
            return data
        final_res = data.copy()
        for each_resource in data.get("resources",  [{}]):
            for each_regex in site_regex:
                pattern = re.compile(each_regex)
                match_res = pattern.match(each_resource.get("name"))
                if not match_res:
                    final_res.get("resources", []).remove(each_resource)
                    continue
        logger.info(f"the {len(final_res.get('resources', []))} site will be handler")
        return final_res

    def __ckeck_lastScanTime(self, data:dict) -> dict:
        # 去除無 Scan Time 的紀錄
        new_resources = [i for i in data.get("resources", [{}]) if ("lastScanTime" in i)]
        data.update({"resources":new_resources})
        # 過濾為更新
        final_res = data.copy()
        path = os.getenv("SCAN_TIME_RECORD")
        record_hash_table = dict()
        # 創建新紀錄
        if(not os.path.exists(path)):
            for each_resource in data.get("resources",  [{}]):
                _id = str(each_resource.get("id", None)) # 不轉可能會重複紀錄
                record_hash_table.update({
                    _id:{
                        "lastScanTime":each_resource.get("lastScanTime"),
                        "name":each_resource.get("name")
                    }
                })
        # 讀取紀錄，更新或跳過
        else:
            with open(path, 'r') as f:
                record_hash_table = json.load(f)
            # resources 資料
            try:
                for each_resource in data.get("resources", [{}]):
                    _id = str(each_resource.get("id", None)) # 不轉可能會重複紀錄
                    if(_id in record_hash_table):
                        if(record_hash_table.get(_id).get("lastScanTime") == each_resource.get("lastScanTime")):
                            final_res.get("resources", []).remove(each_resource)
                        else:
                            record_hash_table.update({
                                _id:{
                                    "lastScanTime":each_resource.get("lastScanTime"),
                                    "name":each_resource.get("name")
                                }
                            })
                    else:
                        record_hash_table.update({
                            _id:{
                                "lastScanTime":each_resource.get("lastScanTime"),
                                "name":each_resource.get("name")
                            }    
                        })
            except AttributeError:
                logger.info("Please check the content of SCAN_TIME_RECORD file is dictionary type")
                raise
        # 覆蓋紀錄
        with open(path, 'w') as f:
            json.dump(record_hash_table, f)
        logger.info(f"the {len(final_res.get('resources', []))} site will be handler")
        # 回傳結果
        return final_res

    def get_sites_detail(self, site_regex:list) -> dict:
        sites_url = ''.join(["https://", self.rapid7_api.url, "/sites"]) # https://10.11.109.101:3780/api/3/sites
        # 第一次取數量
        first_res = self.rapid7_api.requests_get(url=sites_url,auth=self.rapid7_api.auth, verify=False, timeout=10)
        if (not first_res[0]):
            message = "First Site Get info isn,t gotten"
            logger.info(message)
            return {}
        # 紀錄會有多少筆紀錄
        assert isinstance(first_res[1], dict) # 確認
        total_size = first_res[1].get("page", dict()).get("totalResources", 0)
        logger.info(f"get {total_size} site records")
        # 第二次取總結果
        second_res = self.rapid7_api.requests_get(url=sites_url, query_params={'size':total_size}, auth=self.rapid7_api.auth, verify=False, timeout=10)
        if (not second_res[0]):
            message = "Second Site Get info isn,t gotten"
            logger.info(message)
            return {}
        # 去除非指定資料
        res = self.__check_the_site_name_by_regex(second_res[1], site_regex)
        res = self.__ckeck_lastScanTime(res) 
        # 回傳結果
        if(len(res.get('resources', []))):
            return res
        else:
            return {}

    def create_site_entity_set(self, site_resources:list) -> List[Site]:
        sites_entity_set = list()
        for each_site_info in site_resources:
            new_site_entity = Site(each_site_info.get("id"))
            sites_entity_set.append(new_site_entity)
        return sites_entity_set

    def get_assets_detail_and_create_asset_entity_set(self, site:Site, page_size:int) -> dict:
        asset_url = ''.join(["https://", self.rapid7_api.url, "/assets"]) # https://10.11.109.101:3780/api/3/assets 
        asset_info = self.rapid7_api.requests_get(url=asset_url, auth=self.rapid7_api.auth, verify=False, timeout=10)
        if(not asset_info[0] or asset_info[1] == []):
            logger.info(f"Site:{site.id} can,t get the asset number data")
            return {}
        totalresources = int(asset_info[1].get("page", {}).get("totalResources"))
        request_time = (totalresources//page_size) if not (totalresources %
                                                           page_size) else (totalresources//page_size)+1
        asset_list = list()
        for page_number in range(request_time):
            asset_info = self.rapid7_api.requests_get(url=asset_url, query_params={"size":page_size, "page":page_number}, auth=self.rapid7_api.auth, verify=False, timeout=10)
            if(not asset_info[0] or asset_info[1] == []):
                logger.info(f"Site:{site.id} get {page_number}.page data fail")
                return {}
            for each_asset in asset_info[1].get("resources", [{}]):
                new_asset = Asset(site_id=site.id, ip=each_asset.get("ip"))
                time_sort = sorted(each_asset.get('history'), key=lambda k: k.get('version'), reverse=True)# 排序日期
                each_asset.get("history").clear()
                each_asset.get("history").append(time_sort[0])# 更新最新日期

                def _remove_all_links(temp:dict):
                    temp.pop('ip')
                    temp.pop('links')
                    if('services' in temp):
                        for links in temp.get("services"):
                            links.pop('links')
                    return temp

                temp = each_asset.copy()
                temp = _remove_all_links(temp)
                
                new_asset.setting_detail(temp)
                asset_list.append(new_asset)
        
        return asset_list
