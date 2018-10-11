from unittest import mock

from django.test import TestCase

from signals.apps.sigmax.pdf import _generate_pdf, _render_html
from signals.apps.signals import workflow
from tests.apps.signals import factories


class TestPDF(TestCase):

    def test_render_html(self):
        signal = factories.SignalFactoryWithImage.create()
        factories.StatusFactory.create(_signal=signal, state=workflow.AFWACHTING, text='waiting')
        factories.StatusFactory.create(_signal=signal, state=workflow.ON_HOLD, text='please hold')
        status = factories.StatusFactory.create(_signal=signal,
                                                state=workflow.AFGEHANDELD,
                                                text='Consider it done')
        signal.status = status
        signal.save()

        html = _render_html(signal)

        self.assertIn(signal.sia_id, html)
        self.assertIn(signal.category_assignment.sub_category.main_category.name, html)
        self.assertIn(signal.category_assignment.sub_category.name, html)
        self.assertIn(signal.priority.get_priority_display(), html)
        self.assertIn(signal.text, html)
        self.assertIn(signal.location.get_stadsdeel_display(), html)
        self.assertIn(signal.location.address_text, html)
        self.assertIn(signal.source, html)
        self.assertIn('<img src="http://localhost:8000{}'.format(signal.image_crop.url), html)

        for status in signal.statuses.all():
            self.assertIn(status.state, html)
            self.assertIn(status.text, html)
            self.assertIn(status.user, html)

    @mock.patch('signals.apps.sigmax.pdf._render_html')
    @mock.patch('signals.apps.sigmax.pdf.weasyprint')
    def test_generate_pdf(self, mocked_weasyprint, mocked_render_html):
        fake_pdf = b'abc'
        mocked_rendered_html = mock.Mock()
        mocked_weasyprint_html = mock.Mock()
        mocked_weasyprint_html.write_pdf.return_value = fake_pdf
        mocked_render_html.return_value = mocked_rendered_html
        mocked_weasyprint.HTML.return_value = mocked_weasyprint_html

        signal = factories.SignalFactory.create()

        pdf = _generate_pdf(signal)

        mocked_render_html.assert_called_once_with(signal)
        mocked_weasyprint.HTML.assert_called_once_with(string=mocked_rendered_html)
        self.assertEqual(pdf, b'YWJj')  # base64 encoded `fake_pdf`
