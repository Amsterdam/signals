# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from factory import Sequence
from factory.django import DjangoModelFactory

from signals.apps.email_integrations.models import EmailTemplate


class EmailTemplateFactory(DjangoModelFactory):
    class Meta:
        model = EmailTemplate
        django_get_or_create = ('key', )

    key = EmailTemplate.SIGNAL_CREATED
    title = 'Uw melding {{ signal_id }}'
    body = 'Bedankt voor uw melding {{ formatted_signal_id }}!'
    created_by = Sequence(lambda n: 'admin-{}@example.com'.format(n))
