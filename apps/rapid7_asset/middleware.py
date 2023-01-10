import json
import re
import os
import time
from datetime import datetime
from typing import List

from apps.rapid7_asset.data_entity import Asset, Site
from unit_tool.logger_unit import Logger
from apps.rapid7_asset.server import Rapid7API, UploadServer
logger = Logger.debug_level()

class Rapid7Handler():
    """
    作為 Rapid7 服務器 與 Rapid7 資料處理 的中間件
    """
    def  __init__(self) -> None:
        self.rapid7_api = Rapid7API
        self.upload_api = UploadServer

    def setting_rapid7_api_source(self, rapid7_api):
        self.rapid7_api = rapid7_api
    
    def setting_upload_api_source(self, upload_api):
        self.upload_api = upload_api
    
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
                remove_list = list()
                for each_resource in data.get("resources", [{}]):
                    _id = str(each_resource.get("id", None)) # 不轉可能會重複紀錄
                    if(_id in record_hash_table):
                        if(record_hash_table.get(_id).get("lastScanTime") == each_resource.get("lastScanTime")):
                            remove_list.append(each_resource) # 加入白名單內容
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
            # 去除白名單內容
            if(remove_list != []):
                for record in remove_list:
                    final_res.get("resources", [{}]).remove(record)
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
        if(not first_res[0]):
            message = "First Site Get info isn,t gotten"
            logger.info(message)
            return {}
        if(first_res[0] and (first_res[1].json().get("resources", []))==[] ):
            message = "Not get any resource data"
            logger.info(message)
            return {}
        # 紀錄會有多少筆紀錄
        assert isinstance(first_res[1].json(), dict) # 確認
        total_size = first_res[1].json().get("page", dict()).get("totalResources", 0)
        logger.info(f"get {total_size} site records")
        # 第二次取總結果
        second_res = self.rapid7_api.requests_get(url=sites_url, query_params={'size':total_size}, auth=self.rapid7_api.auth, verify=False, timeout=10)
        if (not second_res[0]):
            message = "Second Site Get info isn,t gotten"
            logger.info(message)
            return {}
        # 去除非指定資料
        res = self.__check_the_site_name_by_regex(second_res[1].json(), site_regex)
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
        if(not asset_info[0] or asset_info[1].json()== []):
            logger.info(f"Site:{site.id} can,t get the asset number data")
            return {}
        totalresources = int(asset_info[1].json().get("page", {}).get("totalResources"))
        request_time = (totalresources//page_size) if not (totalresources %
                                                           page_size) else (totalresources//page_size)+1
        asset_list = list()
        for page_number in range(request_time):
            asset_info = self.rapid7_api.requests_get(url=asset_url, query_params={"size":page_size, "page":page_number}, auth=self.rapid7_api.auth, verify=False, timeout=10)
            if(not asset_info[0] or asset_info[1].json() == []):
                logger.info(f"Site:{site.id} get {page_number}.page data fail")
                return {}
            for each_asset in asset_info[1].json().get("resources", [{}]):
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

    def upload_asset_info(self, asset_list:list):
        upload_url = f"http://{self.upload_api.host_port}/assetsmanager/external-src-update/rapid7/"
        for each_asset in asset_list:
            res = self.upload_api.requests_post(upload_url, post_data=each_asset.detail, headers=self.upload_api.headers)
            if(res[0]):
                logger.info(f"asset_{each_asset.ip} data add success")
            else:
                logger.info(f"asset_{each_asset.ip} data add fail")

    def get_rapid7_vul_report_info(self, site:Site):
        def search_scan_id(site_id:int) -> int:
            url = ''.join(["https://", self.rapid7_api.url, f"/sites/{site_id}/scans"]) # https://10.11.109.101:3780/api/3/sites/{id}/scans
            res = self.rapid7_api.requests_get(url, auth=self.rapid7_api.auth, verify=False)
            if(res[0] and res[1].json().get("resources", []) != []):
                scan_id = res[1].json().get("resources")[0].get("id")
                return scan_id
            else:
                logger.info("site_{site_id} get scan_id fail")
                raise

        scan_id = search_scan_id(site.id)

        def get_report_id(scan_id:int) -> int:
            url = f"https://{self.rapid7_api.url}/reports"
            data = {
                "format":"csv-export",
                "name":f"scan_result_{scan_id}_{datetime.now().strftime('%Y/%m/%d, %H:%M:%S')}",
                "scope":{
                    "scan":scan_id
                },
                "template":"export_csv",
                "lauguage":"en-US"
            }
            res = self.rapid7_api.requests_post(url, post_data=data, auth=self.rapid7_api.auth, verify=False)
            if(res[0]):
                report_id = res[1].get('id')
                return report_id
            else:
                logger.info("get report_id fail")
                raise
        
        report_id = get_report_id(scan_id)
        
        def generation_report(report_id:int) -> int:
            url = f"https://{self.rapid7_api.url}/reports/{report_id}/generate"
            res = self.rapid7_api.requests_post(url, post_data=None, auth=self.rapid7_api.auth, verify=False)
            if(res[0]):
                instance_id = res[1].get('id')
                return instance_id
            else:
                logger.info("get instance_id fail")
                raise

        instance_id = generation_report(report_id)

        def check_report_deal_status(report_id:int, instance_id:int) -> bool:
            url = f"https://{self.rapid7_api.url}/reports/{report_id}/history/{instance_id}"
            res = self.rapid7_api.requests_get(url, auth=self.rapid7_api.auth, verify=False)
            if(res[0] and res[1].json().get('status')=="complete"):
                return True
            else:
                time.sleep(0.5)
                return False

        deal_status = False
        while(not deal_status):
            deal_status = check_report_deal_status(report_id, instance_id)
        
        def download_report(site_id:int, report_id:int, instance_id:int):
            url = f"https://{self.rapid7_api.url}/reports/{report_id}/history/{instance_id}/output"
            res = self.rapid7_api.requests_get(url, auth=self.rapid7_api.auth, verify=False)
            if(res[0]):
                save_path = os.path.join(os.getenv("RAPID7_VUL_CSV_FOLDER"), f"rapid7_vul_{site_id}.csv")
                with open(save_path, 'wb') as f:
                    for chunk in res[1].iter_content(chunk_size=8192): 
                        if chunk:
                            f.write(chunk)
            else:
                logger.info("download report fail")
                raise
        
        download_report(site.id, report_id, instance_id)

    def upload_asset_vul_info(self):
        for root, dirs, files in os.walk(os.getenv("RAPID7_VUL_CSV_FOLDER")):
            for each_file in files:
                current_file = os.path.join(root, each_file)
                if(not current_file.endswith(".csv")):
                    continue
                url = f"http://{self.upload_api.host_port}/rapid7/rapid7_vul_csv_upload/"
                post_data_file = {'csv_file': open(current_file,'rb')}
                post_data = {"force":os.getenv("OVERWRITE")}
                res = self.upload_api.requests_post(url, post_data=post_data, headers=self.upload_api.headers, files=post_data_file)
                if(res[0]):
                    logger.info(f"asset_vul_{current_file} csv file upload succcess")
                else:
                    logger.info(f"asset_vul_{current_file} csv file upload fail")
        


