# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Delta10 B.V.
from urllib.parse import urljoin

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.timezone import localtime
import requests
from signals.apps.signals.models.signal import Signal
from signals.celery import app
from signals.apps.signals.workflow import AFGEHANDELD, HEROPEND
from .models import Case


@app.task(autoretry_for=(requests.exceptions.Timeout, requests.exceptions.HTTPError), retry_backoff=True, max_retries=50)
def create_initial(signal_id):
    signal = Signal.objects.get(pk=signal_id)

    context = {
        'signal': signal,
        'url': urljoin(settings.FRONTEND_URL, f'/manage/incident/{signal.id}'),
    }

    data = {
        'bronorganisatie': settings.ZGW_BRONORGANISATIE,
        'omschrijving': render_to_string('case_description.txt', context=context),
        'toelichting': render_to_string('case_explanation.html', context=context),
        'zaaktype': settings.ZGW_ZAAKTYPE,
        'registratiedatum': localtime(signal.created_at).strftime('%Y-%m-%d'),
        'tijdstipRegistratie': localtime(signal.created_at).strftime('%Y-%m-%d  %H:%M'),
        'verantwoordelijkeOrganisatie': settings.ZGW_VERANTWOORDELIJKE_ORGANISATIE,
        'startdatum': localtime(signal.created_at).strftime('%Y-%m-%d'),
        'einddatumGepland': localtime(signal.category_assignment.deadline).strftime('%Y-%m-%d') if signal.category_assignment else signal.created_at.strftime('%Y-%m-%d'),
        'kenmerken': [
            {
                'kenmerk': signal.get_id_display(),
                'bron': 'SIGNALEN'
            }
        ]
    }

    url = urljoin(settings.ZGW_API_URL, '/zgw/zaken')
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()

    case = response.json()

    data = {
        'zaak': case['uuid'],
        'statustype': settings.ZGW_STATUS_RECEIVED,
        'datumStatusGezet': localtime(signal.created_at).strftime('%Y-%m-%d')
    }

    url = urljoin(settings.ZGW_API_URL, '/zgw/statussen')
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()

    Case.objects.update_or_create(external_id=case['uuid'], defaults={
        '_signal': signal
    })


@app.task(autoretry_for=(requests.exceptions.Timeout, requests.exceptions.HTTPError), retry_backoff=True, max_retries=50)
def update_status(signal_id):
    signal = Signal.objects.get(pk=signal_id)

    if signal.status.state != AFGEHANDELD and signal.status.state != HEROPEND:
        return # We only update afgehandeld and heropend

    if not hasattr(signal, 'zgw_case'):
        return  # this Signal is not registered in an external case management system

    data = {
        'zaak': signal.zgw_case.external_id,
        'statustype': settings.ZGW_STATUS_DONE if signal.status.state == AFGEHANDELD else settings.ZGW_STATUS_RECEIVED,
        'datumStatusGezet': localtime(signal.updated_at).strftime('%Y-%m-%d')
    }

    url = urljoin(settings.ZGW_API_URL, '/zgw/statussen')
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()
