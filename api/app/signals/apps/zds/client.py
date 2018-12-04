from django.conf import settings
from zds_client import Client


class ZDSClient:
    def __init__(self):
        Client.load_config(**{
            'zrc': {
                'scheme': settings.ZRC_SCHEME,
                'host': settings.ZRC_HOST,
                'port': settings.ZRC_PORT,
                'auth': settings.ZRC_AUTH,
            },
            'drc': {
                'scheme': settings.DRC_SCHEME,
                'host': settings.DRC_HOST,
                'port': settings.DRC_PORT,
                'auth': settings.DRC_AUTH,
            },
            'ztc': {
                'scheme': settings.ZTC_SCHEME,
                'host': settings.ZTC_HOST,
                'port': settings.ZTC_PORT,
                'auth': settings.ZTC_AUTH,
            }
        })

    def get_client(self, client_type):
        return Client(client_type, base_path='/{}/api/v1/'.format(client_type))

    @property
    def ztc(self):
        return self.get_client('ztc')

    @property
    def zrc(self):
        return self.get_client('zrc')

    @property
    def drc(self):
        return self.get_client('drc')


client = ZDSClient()
