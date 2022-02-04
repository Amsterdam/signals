# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def get_feedback_urls(feedback):
    """Get positive and negative feedback URLs in meldingingen application."""
    positive_feedback_url = f'{settings.FRONTEND_URL}/kto/ja/{feedback.token}'
    negative_feedback_url = f'{settings.FRONTEND_URL}/kto/nee/{feedback.token}'

    return positive_feedback_url, negative_feedback_url
