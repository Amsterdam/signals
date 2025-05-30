# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.

from signals.apps.automation.models import ForwardToExternal, SetState
from signals.apps.automation.utils import make_text_context
from signals.apps.services.domain.dsl import SignalDslService
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal
from signals.celery import app
from django.template import Context, Template

@app.task
def create_initial(signal_id: int) -> None:
    signal = Signal.objects.get(pk=signal_id)

    set_state_rules = SetState.objects.select_related('expression')
    forward_to_external_rules = ForwardToExternal.objects.select_related('expression')

    for set_state_rule in set_state_rules:
        evaluation = SignalDslService().evaluate_expression(signal, set_state_rule.expression)

        if evaluation:
            context = make_text_context(signal)
            message = Template(set_state_rule.text).render(Context(context))

            Signal.actions.update_status({'text': message, 'state': set_state_rule.desired_state}, signal)

            return

    for forward_to_external_rule in forward_to_external_rules:
        evaluation = SignalDslService().evaluate_expression(signal, forward_to_external_rule.expression)

        if evaluation:
            context = make_text_context(signal)
            message = Template(forward_to_external_rule.text).render(Context(context))
            Signal.actions.update_status({'text': message, "email_override": forward_to_external_rule.email, 'send_email': True, 'state': workflow.DOORGEZET_NAAR_EXTERN}, signal)

            return
