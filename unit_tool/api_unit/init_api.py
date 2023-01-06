import requests
import json
from unit_tool.logger_unit import Logger
from datetime import datetime
from typing import Any
logger = Logger.debug_level()

class APIHost(object):
    def __init__(self) -> None:
        self.host = str
        self.port = str
        self.host_port = str
        self.get_data_time = datetime

        self.headers = dict
    
    def setting_host_port(self, host:str, port:int) -> None:
        self.host = host
        self.port = port
        self.host_port = f"{host}:{port}"
    
    def setting_time(self, date_time:datetime) -> None:
        if(date_time):
            self.get_data_time = date_time
        else:
            self.get_data_time = datetime.now()
    
    #!abc
    def setting_headers(self):
        raise NotImplementedError("please define how to setting your headers content")

    @staticmethod
    def combine_url(host:str, path:str, protocol:str="http://") -> str:
        """
        每個 API 呼叫格式可能不一樣
        拼接 protocol host path 成目標網址
        @protocol 預設為 http（通常）
        @host, @path 則為空
        """
        return f"{protocol}{host}/{path}"

    # GET
    @staticmethod
    def requests_get(url:str, query_params:dict=None, headers:dict=None, auth:tuple=None, **kwargs) -> tuple[bool, Any]:
        try:
            res_result = requests.get(url=url, params=query_params, headers=headers, auth=auth, **kwargs)
        except requests.exceptions.ConnectTimeout:
            message = "the request timed out, check the url and try again"
            logger.info(message)
            return False, {"message": message}

        if(res_result.status_code>=200 and res_result.status_code<300):
            return True, res_result
        else:
            message = f"the get url is fail, status_code:{res_result.status_code}"
            logger.info(message)
            logger.debug(res_result.text)
            return False, {"message": message}

    # POST
    @staticmethod
    def requests_post(url:str, post_data:dict=None, headers:dict=None, **kwargs) -> tuple[bool, Any]:
        res_result = requests.post(url=url, json=post_data, headers=headers, **kwargs)
        if(res_result.status_code>=200 and res_result.status_code<300):
            try:
                res_result.json()
            except json.decoder.JSONDecodeError:
                return False, {"message": "request was return 200, but it can,t be json() parsed"}
            return True, res_result.json()
        else:
            message = f"the post url is fail, status_code:{res_result.status_code}"
            logger.info(message)
            logger.debug(res_result.text)
            return False, {"message": f"request status_code {res_result.status_code}"}
    
    # PUT
    @staticmethod
    def requests_put(url:str, put_data:dict, headers:dict, **kwargs) -> tuple[bool, Any]:
        put_data = json.dumps(put_data ,indent=4, sort_keys=True, default=str)
        res_result = requests.put(url=url, data=put_data, headers=headers, **kwargs)
        if(res_result.status_code>=200 and res_result.status_code<300):
            try:
                res_result.json()
            except json.decoder.JSONDecodeError:
                return False, {"message": "request was return 200, but it can,t be json() parsed"}
            return True, res_result.json()
        else:
            message = f"the put url is fail, status_code:{res_result.status_code}"
            logger.info(message)
            logger.debug(res_result.text)
            return False, {"message": f"request status_code {res_result.status_code}"}

        
