# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.questionnaires import tasks
from signals.apps.questionnaires.django_signals import session_frozen


@receiver(session_frozen, dispatch_uid='questionnaires_session_frozen')
def session_frozen_handler(sender, session, *args, **kwargs):
    tasks.update_status_reactie_ontvangen(pk=session.pk)
