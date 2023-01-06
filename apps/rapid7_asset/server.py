from  unit_tool.api_unit import APIHost

class Rapid7API(APIHost):
    """
    代表 Rapid7 服務器層面的實體體現

    Args:
        APIHost (_type_): 從 unit_tool 中繼承 API 基礎類別
    """
    def __init__(self) -> None:
        self.auth = tuple
        self.url = str
        super().__init__()
    
    def setting_headers(self):
        super().setting_headers() # 未實作

    def setting_url(self, url:str):
        self.url = '/'.join([self.host_port, url])

    def setting_auth(self, username:str, password:str):
        self.auth = (username, password)

class UploadServer(APIHost):
    def __init__(self) -> None:
        self.token = str
        super().__init__()
    
    def setting_token(self, token:str):
        self.token = token
    
    def setting_headers(self):
        self.headers = {
            "Auth":self.token
        }
