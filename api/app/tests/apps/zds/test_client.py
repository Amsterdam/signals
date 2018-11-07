from django.test import TestCase

from signals.apps.zds import zds_client


class TestZDSClient(TestCase):

    def test_get_correct_zrc_client(self):
        self.assertEqual(zds_client.zrc.base_url, zds_client.get_client('zrc').base_url)

    def test_get_correct_drc_client(self):
        self.assertEqual(zds_client.drc.base_url, zds_client.get_client('drc').base_url)

    def test_get_correct_ztc_client(self):
        self.assertEqual(zds_client.ztc.base_url, zds_client.get_client('ztc').base_url)
