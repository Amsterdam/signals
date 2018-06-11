# Packages
from rest_framework.test import APITestCase

from . import factories


class BrowseDatasetsTestCase(APITestCase):

    datasets = [
        "signals/signal",
        "signals/status",
        "signals/category",
        "signals/location",
    ]

    def setUp(self):
        self.loc = factories.LocationFactory()
        self.status = factories.StatusFactory()
        self.s = factories.SignalFactory(
            status=self.status,
            location=self.loc)
        self.c = factories.CategoryFactory()
        self.reporter = factories.ReporterFactory()

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
