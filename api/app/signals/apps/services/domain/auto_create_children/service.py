# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import logging

from signals.apps.services.domain.auto_create_children.actions import (
    CreateChildrenContainerAction,
    CreateChildrenEikenprocessierupsAction
)
from signals.apps.signals.models import Signal

log = logging.getLogger(__name__)


class AutoCreateChildrenService:
    actions = (
        CreateChildrenContainerAction(),
        CreateChildrenEikenprocessierupsAction(),
    )

    @staticmethod
    def run(signal_id):
        signal = Signal.objects.get(pk=signal_id)

        for action in AutoCreateChildrenService.actions:
            if action(signal):
                log.info(f'Action {action} ran for Signal #{signal.pk}')
        else:
            log.info(f'No action found to run for Singal #{signal.pk}')
