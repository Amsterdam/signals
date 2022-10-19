# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.conf import settings

MY_SIGNALS_URL = getattr(settings, 'MY_SIGNALS_URL', f'{settings.FRONTEND_URL}/mijn-meldingen')
MY_SIGNALS_LOGIN_URL = getattr(settings, 'MY_SIGNALS_LOGIN_URL', f'{MY_SIGNALS_URL}/login')
MY_SIGNALS_TOKEN_EXPIRES_SECOND = getattr(settings, 'MY_SIGNALS_TOKEN_EXPIRES_SECONDS', 60 * 60 * 2)  # Default 2 hours
