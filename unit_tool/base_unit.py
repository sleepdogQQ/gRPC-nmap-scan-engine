import os
from unit_tool.logger_unit import Logger
logger = Logger.debug_level()

def relocate_program_running_path(file_path):
    """
    讓檔案位置可以在每一次初始化時統一在預計位置（通常就是主程式那層）
    避免在不同路徑運行所導致的路徑錯誤引用
    """
    return os.path.dirname(file_path)

def record_program_process(log:Logger,message):
    """
    紀錄重要程式運行的階段
    通常會同時輸出在 log 與 終端機上
    """
    print(message)
    log.info(message)

def check_file_exist_otherwise_created(file_path):
    """
    檢查檔案是否存在，若不存在則創造
    若發現檔案資料夾不存在也會一起創造
    """
    if(os.path.exists(file_path)):
        return True
    else:
        check_folder_exist_otherwise_created(os.path.dirname(file_path))
        with open(file_path, 'w'): pass
        record_program_process(logger, "the {}_file is created".format(file_path))
        return True
        
def check_folder_exist_otherwise_created(folder_path):
    """
    檢查資料夾是否存在，若不存在則創造
    """
    if(os.path.exists(folder_path)):
        return True
    else:
        os.makedirs(folder_path)
        record_program_process(logger, "the {}_folder is created".format(folder_path))
        return True