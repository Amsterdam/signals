# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import copy

from django.contrib.gis.geos import Point
from django.core import mail
from django.test import TestCase

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.services import MailService
from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.tests.valid_locations import STADHUIS


class TestEmailTemplateAddressFormatting(TestCase):

    def test_address_formatting(self):
        EmailTemplate.objects.create(
            key=EmailTemplate.SIGNAL_CREATED,
            title='Template title {{ signal_id }}',
            body='{{ address|format_address:"O hl, P W" }}',
        )

        valid_location = copy.deepcopy(STADHUIS)
        longitude = valid_location.pop('lon')
        latitude = valid_location.pop('lat')

        signal = SignalFactory.create(
            status__state='m',
            reporter__email='test@example.com',
            location__geometrie=Point(longitude, latitude),
            location__buurt_code=valid_location.pop('buurt_code'),
            location__stadsdeel=valid_location.pop('stadsdeel'),
            location__address=valid_location,
        )

        MailService.mail(signal=signal)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(f'Template title {signal.id}', mail.outbox[0].subject)

        postcode_no_spaces = signal.location.address["postcode"].replace(' ', '')
        postcode = f'{postcode_no_spaces[:4]} {postcode_no_spaces[-2:]}'

        expected_address = f'{signal.location.address["openbare_ruimte"]} {signal.location.address["huisnummer"]}, ' \
                           f'{postcode} {signal.location.address["woonplaats"]}\n\n'
        self.assertEqual(expected_address, mail.outbox[0].body)

    def test_no_address_formatting(self):
        EmailTemplate.objects.create(
            key=EmailTemplate.SIGNAL_CREATED,
            title='Template title {{ signal_id }}',
            body='{% if address %}{{ address|format_address:"O hl, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}'  # noqa
        )

        valid_location = copy.deepcopy(STADHUIS)
        longitude = valid_location.pop('lon')
        latitude = valid_location.pop('lat')

        signal = SignalFactory.create(
            reporter__email='test@example.com',
            location__geometrie=Point(longitude, latitude),
            location__buurt_code=None,
            location__stadsdeel=None,
            location__address=None,
        )

        ma = MailActions(mail_rules=SIGNAL_MAIL_RULES)
        ma.apply(signal_id=signal.id)

        self.assertEqual(f'Template title {signal.id}', mail.outbox[0].subject)
        self.assertEqual('Locatie is gepind op de kaart\n\n', mail.outbox[0].body)
