# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from django.db.models import Q

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.utils import _create_feedback_and_mail_context
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal

SIGNAL_MAIL_RULES = [
    {
        'name': 'Send mail signal created',
        'conditions': {
            'filters': {
                'status__state__in': [workflow.GEMELD, ],
                'reporter__email__isnull': False,
                'reporter__email__gt': 0,
            },
            'functions': {
                'prev_status_gemeld_only_once': lambda signal: signal.statuses.filter(
                    state=workflow.GEMELD
                ).count() == 1,
                'no_children': lambda signal: Signal.objects.filter(id=signal.id).filter(
                    Q(parent_id__isnull=True) | Q(parent__status__state__exact=workflow.GESPLITST)
                )  # SIG-2931, special case for children of split signal --- still needed for historical data
            }
        },
        'kwargs': {
            'key': EmailTemplate.SIGNAL_CREATED,
            'subject': 'Bedankt voor uw melding {signal_id}',
            'context': lambda signal: dict(afhandelings_text=signal.category_assignment.category.handling_message)
        },
        'additional_info': {
            'history_entry_text': 'Automatische e-mail bij registratie van de melding is verzonden aan de melder.'
        }
    },
    {
        'name': 'Send mail signal handled',
        'conditions': {
            'filters': {
                'status__state__in': [workflow.AFGEHANDELD, ],
                'reporter__email__isnull': False,
                'reporter__email__gt': 0,
            },
            'functions': {
                'prev_status_not_in': lambda signal: signal.statuses.exclude(
                    id=signal.status_id
                ).order_by(
                    '-created_at'
                ).values_list(
                    'state',
                    flat=True
                ).first() not in [workflow.VERZOEK_TOT_HEROPENEN, ],
                'no_children': lambda signal: Signal.objects.filter(id=signal.id).filter(
                    Q(parent_id__isnull=True) | Q(parent__status__state__exact=workflow.GESPLITST)
                )  # SIG-2931, special case for children of split signal --- still needed for historical data
            }
        },
        'kwargs': {
            'key': EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD,
            'subject': 'Meer over uw melding {signal_id}',
            'context': lambda signal: _create_feedback_and_mail_context(signal)
        },
        'additional_info': {
            'history_entry_text': 'Automatische e-mail bij afhandelen is verzonden aan de melder.'
        }
    },
    {
        'name': 'Send mail signal scheduled',
        'conditions': {
            'filters': {
                'status__state__in': [workflow.INGEPLAND, ],
                'reporter__email__isnull': False,
                'reporter__email__gt': 0,
            },
            'functions': {
                'no_children': lambda signal: Signal.objects.filter(id=signal.id).filter(
                    Q(parent_id__isnull=True) | Q(parent__status__state__exact=workflow.GESPLITST)
                )  # SIG-2931, special case for children of split signal --- still needed for historical data
            }
        },
        'kwargs': {
            'key': EmailTemplate.SIGNAL_STATUS_CHANGED_INGEPLAND,
            'subject': 'Meer over uw melding {signal_id}'
        },
        'additional_info': {
            'history_entry_text': 'Automatische e-mail bij inplannen is verzonden aan de melder.'
        }
    },
    {
        'name': 'Send mail signal reopened',
        'conditions': {
            'filters': {
                'status__state__in': [workflow.HEROPEND, ],
                'reporter__email__isnull': False,
                'reporter__email__gt': 0,
            },
            'functions': {
                'no_children': lambda signal: Signal.objects.filter(id=signal.id).filter(
                    Q(parent_id__isnull=True) | Q(parent__status__state__exact=workflow.GESPLITST)
                )  # SIG-2931, special case for children of split signal --- still needed for historical data
            }
        },
        'kwargs': {
            'key': EmailTemplate.SIGNAL_STATUS_CHANGED_HEROPEND,
            'subject': 'Meer over uw melding {signal_id}'
        },
        'additional_info': {
            'history_entry_text': 'Automatische e-mail bij heropenen is verzonden aan de melder.'
        }
    },
    # SIG-2932
    {
        'name': 'Send mail optional',
        'conditions': {
            'filters': {
                'reporter__email__isnull': False,
                'reporter__email__gt': 0,
                'status__state__in': [
                    workflow.GEMELD,  # no need for extra filtering, send_mail=True is enough
                    workflow.AFWACHTING,
                    workflow.BEHANDELING,
                    workflow.ON_HOLD,
                    workflow.VERZOEK_TOT_AFHANDELING,
                    workflow.GEANNULEERD,  # TODO: do we GEANNULEERD to send emails?
                ],
                'status__send_email__exact': True,  # on create_initial this is False (model default)
            },
            'functions': {
                'no_children': lambda signal: Signal.objects.filter(id=signal.id).filter(
                    Q(parent_id__isnull=True) | Q(parent__status__state__exact=workflow.GESPLITST)
                )  # SIG-2931, special case for children of split signal --- still needed for historical data
            }
        },
        'kwargs': {
            'key': EmailTemplate.SIGNAL_STATUS_CHANGED_OPTIONAL,
            'subject': 'Meer over uw melding {signal_id}',
            'context': lambda signal: dict(afhandelings_text=signal.status.text)
        },
        'additional_info': {
            'history_entry_text': 'De statusupdate is per e-mail verzonden aan de melder'
        }
    }
]
