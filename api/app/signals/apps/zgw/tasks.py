# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Delta10 B.V.
from urllib.parse import urljoin

import celery
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.timezone import localtime
import requests
from signals.apps.signals.models import Signal, Status
from signals.celery import app
from signals.apps.signals.workflow import GEMELD, HEROPEND, AFGEHANDELD, GEANNULEERD
from .models import Case


MAX_RETRIES = 100
DEFAULT_RETRY_DELAY = 60*10

AUTORETRY_FOR = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.HTTPError
)


@app.task(autoretry_for=AUTORETRY_FOR, max_retries=MAX_RETRIES, default_retry_delay=DEFAULT_RETRY_DELAY)
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

    Case.objects.update_or_create(external_id=case['uuid'], defaults={
        '_signal': signal
    })

    # Trigger async job to set current status of Signal
    app.send_task('signals.apps.zgw.tasks.update_status', args=[signal.status.pk])


@app.task(autoretry_for=AUTORETRY_FOR, max_retries=MAX_RETRIES, default_retry_delay=DEFAULT_RETRY_DELAY)
def update_status(status_id):
    status = Status.objects.get(pk=status_id)
    signal = status._signal

    if not hasattr(signal, 'zgw_case'):
        return  # this Signal is not registered in an external case management system

    zgw_states = {
        GEMELD: settings.ZGW_STATUS_RECEIVED,
        HEROPEND: settings.ZGW_STATUS_RECEIVED,
        AFGEHANDELD: settings.ZGW_STATUS_DONE,
        GEANNULEERD: settings.ZGW_STATUS_DONE
    }

    data = {
        'zaak': signal.zgw_case.external_id,
        'statustype': zgw_states[status.state],
        'datumStatusGezet': localtime(status.created_at).strftime('%Y-%m-%d')
    }

    url = urljoin(settings.ZGW_API_URL, '/zgw/statussen')
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()
