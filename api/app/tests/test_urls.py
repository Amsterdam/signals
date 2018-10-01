from django.test import TestCase


class TestURLs(TestCase):

    def test_swagger_index(self):
        url = '/signals/swagger/?format=openapi'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
