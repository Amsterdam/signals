# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Support for "reactie melder" flow.

This flow allows Signalen users to request extra information from a reporter
whose signal/complaint does not have all information that is required to handle
it. This assumes the reported signal/complaint was not anonymous, and that
an email address was available.
"""

from signals.apps.questionnaires.exceptions import WrongState
from signals.apps.signals import workflow

class ReactionRequestService:
    @staticmethod
    def create_reaction_request(signal):
        if signal.status.state !=  workflow.REACTIE_GEVRAAGD:
            msg = f'Signal {signal.id} is not in state REACTIE_GEVRAAGD!'
            raise WrongState()