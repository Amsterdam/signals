from unittest import mock

from django.test import TestCase
from django.utils import timezone

from signals.apps.sigmax.pdf import _generate_pdf, _render_html
from signals.apps.signals import workflow
from tests.apps.signals import factories


class TestPDF(TestCase):

    def test_render_html(self):
        extra_properties_data = {
            'Extra vraag': 'Extra antwoord'
        }
        signal = factories.SignalFactoryWithImage.create(
            incident_date_start=timezone.now(),
            extra_properties=extra_properties_data,
            reporter__email='foo@bar.com',
            reporter__phone='0612345678')
        factories.StatusFactory.create(_signal=signal, state=workflow.AFWACHTING, text='waiting')
        factories.StatusFactory.create(_signal=signal, state=workflow.ON_HOLD, text='please hold')
        status = factories.StatusFactory.create(_signal=signal,
                                                state=workflow.AFGEHANDELD,
                                                text='Consider it done')
        signal.status = status
        signal.save()

        html = _render_html(signal)

        # General information about the `Signal` object.
        current_tz = timezone.get_current_timezone()
        self.assertIn(signal.sia_id, html)
        self.assertIn(signal.created_at.astimezone(current_tz).strftime('%d-%m-%Y'), html)
        self.assertIn(signal.created_at.astimezone(current_tz).strftime('%H:%M:%S'), html)
        self.assertIn(signal.incident_date_start.astimezone(current_tz).strftime('%d-%m-%Y'), html)
        self.assertIn(signal.incident_date_start.astimezone(current_tz).strftime('%H:%M:%S'), html)
        self.assertIn(signal.sia_id, html)
        self.assertIn(signal.category_assignment.category.parent.name, html)
        self.assertIn(signal.category_assignment.category.name, html)
        self.assertIn(signal.priority.get_priority_display(), html)
        self.assertIn(signal.text, html)
        self.assertIn(signal.location.get_stadsdeel_display(), html)
        self.assertIn(signal.location.address_text, html)
        self.assertIn(signal.source, html)

        # Reporter information.
        self.assertIn(signal.reporter.email, 'foo@bar.com')
        self.assertIn(signal.reporter.phone, '0612345678')

        # All status transitions.
        for status in signal.statuses.all():
            self.assertIn(status.state, html)
            self.assertIn(status.text, html)
            self.assertIn(status.user, html)

        # Extra properties
        for key, value in extra_properties_data.items():
            self.assertIn(key, html)
            self.assertIn(value, html)

        # Uploaded photo.
        self.assertIn('<img src="http://localhost:8000{}'.format(signal.image_crop.url), html)

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
