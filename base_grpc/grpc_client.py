import grpc
import os

# 先把 Token 寫在這，好理解
_ACCESS_TOKEN = "systex_token"

# 與 server 相同
class SSLCredentialsMixin:
    CRT_PATH = None
    _SERVER_CERTIFICATE = None

    def __init__(self) -> None:
        self.load_credentials()

    def load_credentials(self):
        '''
        讀取 SSL 憑證檔案
        '''
        with open(self.CRT_PATH, 'rb') as f:
            self._SERVER_CERTIFICATE = f.read()

class AuthGateway(grpc.AuthMetadataPlugin):

    def __call__(self, context, callback):
        signature = context.method_name[::-1]
        callback(((_ACCESS_TOKEN, signature),), None)

class BasegRPClient(SSLCredentialsMixin):
    CRT_PATH  = os.getenv("GRPC_CRT_PATH")

    def __init__(self,host:str, port:int):
        self.host = host
        self.port = port
        self.composite_credentials = self.setting_ssl()

        super().__init__()
        super(SSLCredentialsMixin, self).__init__()


    def setting_ssl(self):
        call_credentials = grpc.metadata_call_credentials(
            AuthGateway(), name='auth gateway')

        with open(self.CRT_PATH) as f:
            trusted_certs = f.read().encode()

        # create SSL credentials
        channel_credentials = grpc.ssl_channel_credentials(
            root_certificates=trusted_certs)

        # 組合成複合 credentials
        composite_credentials = grpc.composite_channel_credentials(
            channel_credentials,
            call_credentials,
        )

        return composite_credentials

    def run(self) -> grpc.Channel:
        """
        回傳 grpc.Channel
        """
        return grpc.secure_channel(f'{self.host}:{self.port}', self.composite_credentials)
        