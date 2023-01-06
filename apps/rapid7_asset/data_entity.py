class Asset(object):
    """
    代表 asset 的資料型態
    """
    def __init__(self, site_id:int, ip:str):
        self.site_id = site_id
        self.ip = ip
        self.detail = dict()
    
    def setting_detail(self, detail:dict):
        self.detail = detail

class Site():
    """
    代表 Site 的資料型態
    """
    def __init__(self, id:int):
        self.id = id
        self.belong_asset = list()
        self.belong_report_info = tuple()
        
    def add_belong_asset_data(self, asset_list:list):
        self.belong_asset.extend(asset_list)
    
    def setting_belong_report_info_data(self, vul_report_id:int, vul_instance_id:int):
        self.vul_report_id = vul_report_id
        self.vul_instance_id = vul_instance_id
