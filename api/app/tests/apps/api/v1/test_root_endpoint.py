import os

from signals import API_VERSIONS
from signals.utils.version import get_version
from tests.test import SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)
SIGNALS_TEST_DIR = os.path.join(os.path.split(THIS_DIR)[0], '..', 'signals')


class TestAPIRoot(SignalsBaseApiTestCase):

    def test_http_header_api_version(self):
        response = self.client.get('/signals/v1/')

        self.assertEqual(response['X-API-Version'], get_version(API_VERSIONS['v1']))
