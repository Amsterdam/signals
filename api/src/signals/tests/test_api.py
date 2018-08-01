"""
Test gets basic endpoints and authorization
"""
# Packages
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase

from signals.models import Signal
from . import factories


class BrowseDatasetsTestCase(APITestCase):
    datasets = [
        "signals/auth/signal",
        "signals/auth/status",
        "signals/auth/category",
        "signals/auth/location",
    ]

    def setUp(self):
        self.s = factories.SignalFactory()

        self.loc = factories.LocationFactory(_signal=self.s)
        self.status = factories.StatusFactory(_signal=self.s)
        self.category = factories.CategoryFactory(_signal=self.s)
        self.reporter = factories.ReporterFactory(_signal=self.s)

        self.s.location = self.loc
        self.s.status = self.status
        self.s.category = self.category
        self.s.reporter = self.reporter
        self.s.save()

    def valid_html_response(self, url, response):
        """
        Helper method to check common status/json
        """

        self.assertEqual(
            200, response.status_code, "Wrong response code for {}".format(url)
        )

        self.assertEqual(
            "text/html; charset=utf-8",
            response["Content-Type"],
            "Wrong Content-Type for {}".format(url),
        )

    def test_index_pages(self):
        url = "signals"

        response = self.client.get("/{}/".format(url))

        self.assertEqual(
            response.status_code, 200, "Wrong response code for {}".format(url)
        )

    def test_lists(self):
        for url in self.datasets:
            response = self.client.get("/{}/".format(url))

            self.assertEqual(
                response.status_code, 200,
                "Wrong response code for {}".format(url)
            )

            self.assertEqual(
                response["Content-Type"],
                "application/json",
                "Wrong Content-Type for {}".format(url),
            )

            self.assertIn(
                "count", response.data, "No count attribute in {}".format(url)
            )

    def test_lists_html(self):
        for url in self.datasets:
            response = self.client.get("/{}/?format=api".format(url))

            self.valid_html_response(url, response)

            self.assertIn(
                "count", response.data, "No count attribute in {}".format(url)
            )

    def test_signal_unauthenticated(self):
        some_signal = Signal.objects.all().first()

        response = self.client.get(f"/signals/signal/{some_signal.signal_id}/")
        self.assertEqual(response.status_code, HTTP_200_OK,
                         "Probelem retrieving signal status")
        self.assertEqual(response.data.get('signal_id'),
                         str(some_signal.signal_id),
                         "Signaal komt niet overeen")
        self.assertEqual(response.data.get('status').get('id'),
                         some_signal.status.id, "Status id komt niet overeen")
        self.assertEqual(response.data.get('status').get('state'),
                         str(some_signal.status.state),
                         "Signaal status komt niet overeen")
        self.assertEqual(response.data.get('text'), None,
                         "Signaal lekt informatie naar publiek endpoint")
        self.assertEqual(response.data.get('category'), None,
                         "Signaal lekt informatie naar publiek endpoint")
        self.assertEqual(response.data.get('location'), None,
                         "Signaal lekt informatie naar publiek endpoint")
        self.assertEqual(response.data.get('id'), None,
                         "Signaal lekt informatie naar publiek endpoint")
