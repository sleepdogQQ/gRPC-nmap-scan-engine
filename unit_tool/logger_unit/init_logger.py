import os
import yaml
import logging
import logging.config

# Filter example
class LevelFilter(logging.Filter):
    def filter(self, record):
        if record.levelno < logging.WARNING:
            return False
        return True

class Logger:
    def __init__(self):
        pass
 
    @classmethod
    def info_level(cls, default_path=os.getenv("LOGGER_SETTING"), default_level=logging.INFO):
        path = default_path
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            logging.config.dictConfig(config)
            return logging.getLogger('info_module')
 
    @classmethod
    def debug_level(cls, default_path=os.getenv("LOGGER_SETTING"), default_level=logging.DEBUG):
        path = default_path
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            logging.config.dictConfig(config)
            return logging.getLogger('debug_module')
 
    @classmethod
    def error_level(cls, default_path=os.getenv("LOGGER_SETTING"), default_level=logging.ERROR):
        path = default_path
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            logging.config.dictConfig(config)
            return logging.getLogger()
            