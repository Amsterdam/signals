# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import logging
from typing import Dict

from django.conf import settings
from django.db.models import Q

from signals.apps.feedback.models import StandardAnswer

logger = logging.getLogger(__name__)


def get_feedback_urls(feedback):
    """Get positive and negative feedback URLs in meldingingen application."""
    positive_feedback_url = f'{settings.FRONTEND_URL}/kto/ja/{feedback.token}'
    negative_feedback_url = f'{settings.FRONTEND_URL}/kto/nee/{feedback.token}'

    return positive_feedback_url, negative_feedback_url


def validate_answers(data: Dict) -> bool:
    """
    Validate if the answers require the signal to be reopened or not
    """
    text_list = set(data.get('text_list', []))
    query = Q()
    for t in text_list:
        query.add(Q(text=t), Q.OR)

    sa = StandardAnswer.objects.filter(query)
    if len(sa) != len(text_list):
        # if the lists are not of equal length the list has custom texts and needs to be reopend
        return True

    return any(x for x in sa if x.reopens_when_unhappy)


def merge_texts(data: Dict) -> Dict:
    """
    Merge the text and text_list to only text_list and return the new list
    """
    text_list = data.get('text_list') if data.get('text_list') else []

    text = data.pop('text', None)
    if text:
        text_list.append(text)

    data['text_list'] = text_list
    return data
