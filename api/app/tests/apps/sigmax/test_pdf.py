from unittest import mock

from django.test import TestCase

from signals.apps.sigmax.pdf import _render_html
from tests.apps.signals import factories


class TestPDF(TestCase):

    def test_render_html_without_image(self):
        signal = factories.SignalFactory.create()

        html = _render_html(signal)

        self.assertIn(signal.sia_id, html)
        self.assertIn(signal.category_assignment.sub_category.main_category.name, html)
        self.assertIn(signal.category_assignment.sub_category.name, html)
        self.assertIn(signal.priority.get_priority_display(), html)
        self.assertIn(signal.text, html)
        self.assertIn(signal.location.get_stadsdeel_display(), html)
        self.assertIn(signal.location.address_text, html)
        self.assertIn(signal.source, html)

    def test_render_html_with_local_image(self):
        signal = factories.SignalFactoryWithImage.create()

        html = _render_html(signal)

        self.assertIn('<img src="http://localhost:8000/{}'.format(signal.image.url), html)

    @mock.patch('signals.apps.sigmax.pdf.isinstance', return_value=True)
    def test_render_html_with_swift_image(self, mocked_isinstance):
        signal = factories.SignalFactory.create()
        signal.image = mock.Mock(url='url/to/image.jpg')

        html = _render_html(signal)

        self.assertIn('<img src="url/to/image.jpg'.format(signal.image.url), html)
