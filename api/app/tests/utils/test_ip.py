from django.test import RequestFactory, TestCase

from signals.utils.ip import get_ip


class TestIP(TestCase):

    def setUp(self):
        self.request = RequestFactory()

    def test_get_ip_x_forwared_for(self):
        request = self.request.get('/', HTTP_X_FORWARDED_FOR='1.2.3.4')
        request.get_token_subject = 'token'
        ip = get_ip(request)

        self.assertEqual(ip, '1.2.3.4')

    def test_get_ip_remote_addr(self):
        request = self.request.get('/')
        request.get_token_subject = 'token'
        ip = get_ip(request)

        self.assertEqual(ip, '127.0.0.1')

    def test_get_ip_non_get_token_subject(self):
        request = self.request.get('/')
        self.assertIsNone(get_ip(request))

    def test_get_ip_non_request(self):
        self.assertIsNone(get_ip(None))
