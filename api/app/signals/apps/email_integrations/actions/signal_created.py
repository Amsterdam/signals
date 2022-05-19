# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalCreatedRule

logger = logging.getLogger(__name__)


class SignalCreatedAction(AbstractAction):
    rule = SignalCreatedRule()

    key = EmailTemplate.SIGNAL_CREATED
    subject = 'Bedankt voor uw melding {formatted_signal_id}'

    note = 'Automatische e-mail bij registratie van de melding is verzonden aan de melder.'

    def get_additional_context(self, signal, dry_run=False):
        context = {'afhandelings_text': signal.category_assignment.category.handling_message, }

        if signal.reporter and signal.reporter.phone:
            """
            If a reporter has given his/hers phone number it is added to the email context in a specific format.
            Examples:
                - +31 6 12 34 56 78 -> *******678
                - +31612345678      -> *******678
                - 06 12 34 56 78    -> *******678
                - 0612345678        -> *******678
            """
            reporter_phone = signal.reporter.phone.replace(' ', '')
            reporter_phone = reporter_phone[-3:].rjust(10, '*').replace('*', '\\*')  # noqa escape the * because it is used in markdown
            context.update({'reporter_phone': reporter_phone})

        if signal.reporter and signal.reporter.email:
            """
            If a reporter has given his/hers email address it is added to the email context in a specific format.
            Examples:
                - test@test.com         -> t**t@***t.com
                - test.user@gmail.com   -> t*******r@****l.com
                - test.user@amsterdam.nl-> t*******r@********m.nl
                - test@tst.com          -> t**t@***.com
                - tt@tst.com            -> tt@***.com
            """
            local, domain = signal.reporter.email.split('@')
            local = local[0].ljust(len(local)-1, '*') + local[-1]
            sd, tld = domain[:domain.rfind('.')], domain[domain.rfind('.'):]
            sd = sd[-1:].rjust(len(sd), '*') if len(sd) > 3 else ''.join(['*' for _ in range(len(sd))])

            reporter_email = f'{local}@{sd}{tld}'.replace('*', '\\*')  # noqa escape the * because it is used in markdown
            context.update({'reporter_email': reporter_email})

        # Add the extra properties to the context of the email template
        context.update({'extra_properties': self._extra_properties_context(signal.extra_properties)})

        return context

    def _extra_properties_context(self, extra_properties):
        """
        Renders the extra properties of the signals as a dict of key-value pairs so that they can be rendered in the
        email template.
        """
        if not extra_properties:
            return {}

        context = {}
        for extra_property in extra_properties:
            context[extra_property['label']] = []
            if isinstance(extra_property['answer'], (list, tuple)):
                for answer in extra_property['answer']:
                    context[extra_property['label']].append(self._get_answer_from_extra_property(answer))
            else:
                context[extra_property['label']].append(self._get_answer_from_extra_property(extra_property['answer']))
        return context

    def _get_answer_from_extra_property(self, extra_property):
        """
        Returns the first option that is available in the extra property and not empty as the answer.
        Defaults to '-' if no option is available.
        """
        if isinstance(extra_property, str):
            return extra_property
        elif 'label' in extra_property and extra_property['label']:
            return extra_property['label']
        elif 'value' in extra_property and extra_property['value']:
            return extra_property['value']
        elif 'answer' in extra_property and extra_property['answer']:
            return extra_property['answer']
        elif 'id' in extra_property and extra_property['id']:
            return extra_property['id']
        elif 'type' in extra_property and extra_property['type']:
            return extra_property['type']
        elif extra_property:
            return extra_property
        else:
            return '-'
