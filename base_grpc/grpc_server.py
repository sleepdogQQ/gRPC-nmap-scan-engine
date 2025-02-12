# date: 2022/12/09
# author: AxelHowe
import grpc
from concurrent import futures
from unit_tool.logger_unit import Logger
from unit_tool.base_unit import record_program_process

logger = Logger.debug_level()

class SSLCredentialsMixin:
    CRT_PATH = None
    KEY_PATH = None
    _SERVER_CERTIFICATE = None
    _SERVER_CERTIFICATE_KEY = None

    def __init__(self) -> None:
        self.load_credentials()

    def load_credentials(self):
        '''
        讀取 SSL 憑證檔案
        '''
        try:
            with open(self.CRT_PATH, 'rb') as f:
                self._SERVER_CERTIFICATE = f.read()
            with open(self.KEY_PATH, 'rb') as f:
                self._SERVER_CERTIFICATE_KEY = f.read()
        except TypeError as e:
            message = f"the CRT_PATH or KEY_PATH still is None, please confime the env is useful"
            record_program_process(logger, message)
            raise e
        except FileNotFoundError as e:
            message = f"not find the credentials *({self.CRT_PATH}) or *({self.KEY_PATH}), please check the file is exist"
            record_program_process(logger, message)
            raise e
class BasegRPCServer:

    _SERVER = None

    def __init__(self, host, port) -> None:
        self.host = host
        self.port = port
        
    def setting_base_config(self, setting_config:dict):
        self.max_workers = setting_config.get("max_workers", 10)
        self.interceptors = setting_config.get("interceptors", tuple())

    def init_server_beforce_run(self):
        """
        最好是已經有執行過 setting_base_config 再進行此函式
        """
        thread_pool = futures.ThreadPoolExecutor(self.max_workers)
        self._SERVER = grpc.server(
            thread_pool,
            interceptors=self.interceptors
        )
    
    def register_service(self):
        '''
        寫好的 service 在這裡宣告
        '''
        pass

    def setting_reflection(self):
        """
        反射功能宣告
        """
        pass

    def run_without_ssl(self):
        '''
        沒有 SSL 憑證
        '''
        self._SERVER.add_insecure_port(f'{self.host}:{self.port}')
        self._SERVER.start()
        self._SERVER.wait_for_termination()
    
class SSLgRPCServer(BasegRPCServer,
                    SSLCredentialsMixin):

    def __init__(self, host, port) -> None:
        super().__init__(host, port)
        super(BasegRPCServer, self).__init__()
        super(SSLCredentialsMixin, self).__init__()

    def run_with_ssl(self):
        '''
        有 SSL 憑證
        '''
        channel_credential = grpc.ssl_server_credentials(((
            self._SERVER_CERTIFICATE_KEY,
            self._SERVER_CERTIFICATE,
        ),))
        self._SERVER.add_secure_port(f'{self.host}:{self.port}', channel_credential)
        self._SERVER.start()
        self._SERVER.wait_for_termination()

