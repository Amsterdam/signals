# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.http import Http404

from signals.apps.questionnaires.models import Session
from signals.apps.questionnaires.services.utils import get_session_service


def get_session_service_or_404(session):
    """
    Based on Django's get_object_or_404 as implemented in django.shortcuts.get_object_or_404
    """
    try:
        return get_session_service(session)
    except Session.DoesNotExist:
        raise Http404
