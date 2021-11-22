# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from signals.apps.sigmax.stuf_protocol.outgoing.pdf import _generate_pdf, _render_html
from signals.apps.signals import factories, workflow


class TestPDF(TestCase):

    def test_render_html(self):
        extra_properties_data = [
            {
                "id": "extra_straatverlichting",
                "label": "Is de situatie gevaarlijk?",
                "answer": {
                    "id": "niet_gevaarlijk",
                    "label": "Niet gevaarlijk"
                },
                "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting"  # noqa
            },
            {
                "id": "niet_in_de_pdf",
                "label": "Staat deze vraag in de PDF?",
                "answer": {
                    "id": "niet_in_de_pdf",
                    "label": "Nee deze staat niet in de PDF"
                },
                "category_url": "/signals/v1/public/terms/categories/overig/sub_categories/overig"
                # noqa
            },
        ]
        signal = factories.SignalFactoryWithImage.create(
            incident_date_start=timezone.now(),
            extra_properties=extra_properties_data,
            category_assignment__category__parent__name='Wegen, verkeer, straatmeubilair',
            category_assignment__category__name='lantaarnpaal straatverlichting',
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
        self.assertIn(f'Signalen-{signal.id}', html)
        self.assertIn(signal.created_at.astimezone(current_tz).strftime('%d-%m-%Y'), html)
        self.assertIn(signal.created_at.astimezone(current_tz).strftime('%H:%M:%S'), html)
        self.assertIn(signal.incident_date_start.astimezone(current_tz).strftime('%d-%m-%Y'), html)
        self.assertIn(signal.incident_date_start.astimezone(current_tz).strftime('%H:%M:%S'), html)
        self.assertIn(f'Signalen-{signal.id}', html)
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
        self.assertIn('Is de situatie gevaarlijk?', html)
        self.assertIn('Niet gevaarlijk', html)

        self.assertNotIn('Staat deze vraag in de PDF?', html)
        self.assertNotIn('Nee deze staat niet in de PDF', html)

        # # Uploaded photo.
        # images = signal.attachments.filter(is_image=True)
        # for image in images:
        #     self.assertIn('<img src="{}'.format(image.file.url), html)

    @mock.patch('signals.apps.sigmax.stuf_protocol.outgoing.pdf._render_html')
    @mock.patch('signals.apps.sigmax.stuf_protocol.outgoing.pdf.weasyprint')
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
