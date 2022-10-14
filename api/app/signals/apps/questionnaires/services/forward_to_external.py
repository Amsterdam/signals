# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def create_session_for_forward_to_external(signal):
    # HIERZO!!!
    pass


def get_forward_to_external_url(session):
    return f'{settings.FRONTEND_URL}/incident/extern/{session.uuid}'
