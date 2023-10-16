# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
import typing

from signals.apps.email_integrations.actions.abstract import AbstractSignalStatusAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalCreatedRule
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.services.domain.contact_details import ContactDetailsService
from signals.apps.signals.models import Signal


class SignalCreatedAction(AbstractSignalStatusAction):
    rule: AbstractRule = SignalCreatedRule()

    key: str = EmailTemplate.SIGNAL_CREATED
    subject: str = 'Bedankt voor uw melding {formatted_signal_id}'

    note: str = 'Automatische e-mail bij registratie van de melding is verzonden aan de melder.'

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        assert signal.category_assignment is not None

        context = {'afhandelings_text': signal.category_assignment.category.handling_message, }

        if signal.reporter:
            if signal.reporter.phone:
                """
                If a reporter has given his/hers phone number it is added to the email context in a specific format.
                """
                context.update({'reporter_phone': ContactDetailsService.obscure_phone(signal.reporter.phone, True)})

            if signal.reporter.email:
                """
                If a reporter has given his/hers email address it is added to the email context in a specific format.
                """
                context.update({'reporter_email': ContactDetailsService.obscure_email(signal.reporter.email, True)})

            context.update({'reporter_sharing_allowed': signal.reporter.sharing_allowed})

        # Add the extra properties to the context of the email template
        context.update({'extra_properties': self._extra_properties_context(signal.extra_properties)})

        return context

    def _extra_properties_context(self, extra_properties: list) -> dict:
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

    def _get_answer_from_extra_property(self, extra_property: typing.Union[str, dict]) -> str: # noqa C901
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
        elif set(extra_property.keys()) == {'location'}:
            # Hacky solution that will be refactored when Questionnaires will be in use.
            #
            # Sometimes it happens the extra_properties of a selected object only contains a location
            # In this case we want to show "Locatie gepind op de kaart"
            return 'Locatie gepind op de kaart'
        elif extra_property:
            return extra_property
        else:
            return '-'
