"""
Test gets basic endpoints and authorization
"""
# Packages
from rest_framework.test import APITestCase

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
        self.c = factories.CategoryFactory(_signal=self.s)
        self.reporter = factories.ReporterFactory(_signal=self.s)

        self.status.signal.add(self.s),
        self.loc.signal.add(self.s)
        self.c.signal.add(self.s)
        self.reporter.signal.add(self.s)

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
