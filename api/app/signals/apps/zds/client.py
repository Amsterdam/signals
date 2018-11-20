from django.conf import settings
from zds_client import Client


class ZDSClient:
    def __init__(self):
        Client.load_config(settings.ROOT_DIR, **{
            'zrc': {
                'scheme': settings.ZRC_SCHEME,
                'host': settings.ZRC_HOST,
                'port': settings.ZRC_PORT,
            },
            'drc': {
                'scheme': settings.DRC_SCHEME,
                'host': settings.DRC_HOST,
                'port': settings.DRC_PORT,
            },
            'ztc': {
                'scheme': settings.ZTC_SCHEME,
                'host': settings.ZTC_HOST,
                'port': settings.ZTC_PORT,
            }
        })

    def get_client(self, type):
        return Client(type)

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
