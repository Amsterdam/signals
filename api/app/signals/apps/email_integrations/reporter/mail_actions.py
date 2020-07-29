import copy
from typing import Any

from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.db.models import Q
from django.template import loader
from django.utils.text import slugify

from signals.apps.signals.models import Signal
from signals.apps.signals.workflow import (
    AFGEHANDELD,
    AFWACHTING,
    BEHANDELING,
    GEANNULEERD,
    GEMELD,
    GESPLITST,
    HEROPEND,
    INGEPLAND,
    ON_HOLD,
    VERZOEK_TOT_AFHANDELING,
    VERZOEK_TOT_HEROPENEN
)

SIGNAL_MAIL_RULES = [
    {
        'name': 'Send mail signal created',
        'conditions': {
            'filters': {
                'status__state__in': [GEMELD, ],
                'reporter__email__isnull': False,
                'reporter__email__gt': 0,
            },
            'functions': {
                'prev_status_gemeld_only_once': lambda signal: signal.statuses.filter(state=GEMELD).count() == 1,
                'no_children': lambda signal: Signal.objects.filter(id=signal.id).filter(
                    Q(parent_id__isnull=True) | Q(parent__status__state__exact=GESPLITST)
                )  # SIG-2931, special case for children of split signal
            }
        },
        'kwargs': {
            'subject': 'Bedankt voor uw melding ({signal_id})',
            'templates': {
                'txt': 'email/signal_created.txt',
                'html': 'email/signal_created.html'
            },
            'context': lambda signal: dict(afhandelings_text=signal.category_assignment.category.handling_message)
        }
    },
    {
        'name': 'Send mail signal handled',
        'conditions': {
            'filters': {
                'status__state__in': [AFGEHANDELD, ],
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
                        ).first() not in [VERZOEK_TOT_HEROPENEN, ],
                'no_children': lambda signal: Signal.objects.filter(id=signal.id).filter(
                    Q(parent_id__isnull=True) | Q(parent__status__state__exact=GESPLITST)
                )  # SIG-2931, special case for children of split signal
            }
        },
        'kwargs': {
            'subject': 'Betreft melding: {signal_id}',
            'templates': {
                'txt': 'email/signal_status_changed_afgehandeld.txt',
                'html': 'email/signal_status_changed_afgehandeld.html'
            },
            'context': lambda signal: _create_feedback_and_mail_context(signal)
        }
    },
    {
        'name': 'Send mail signal split',
        'conditions': {
            'filters': {
                'status__state__in': [GESPLITST, ],
                'reporter__email__isnull': False,
                'reporter__email__gt': 0,
            },
            'functions': {
                'no_children': lambda signal: Signal.objects.filter(id=signal.id).filter(
                    Q(parent_id__isnull=True) | Q(parent__status__state__exact=GESPLITST)
                )  # SIG-2931, special case for children of split signal
            }
        },
        'kwargs': {
            'subject': 'Betreft melding: {signal_id}',
            'templates': {
                'txt': 'email/signal_split.txt',
                'html': 'email/signal_split.html'
            }
        }
    },
    {
        'name': 'Send mail signal scheduled',
        'conditions': {
            'filters': {
                'status__state__in': [INGEPLAND, ],
                'reporter__email__isnull': False,
                'reporter__email__gt': 0,
            },
            'functions': {
                'no_children': lambda signal: Signal.objects.filter(id=signal.id).filter(
                    Q(parent_id__isnull=True) | Q(parent__status__state__exact=GESPLITST)
                )  # SIG-2931, special case for children of split signal
            }
        },
        'kwargs': {
            'subject': 'Betreft melding: {signal_id}',
            'templates': {
                'txt': 'email/signal_status_changed_ingepland.txt',
                'html': 'email/signal_status_changed_ingepland.html'
            }
        }
    },
    {
        'name': 'Send mail signal reopened',
        'conditions': {
            'filters': {
                'status__state__in': [HEROPEND, ],
                'reporter__email__isnull': False,
                'reporter__email__gt': 0,
            },
            'functions': {
                'no_children': lambda signal: Signal.objects.filter(id=signal.id).filter(
                    Q(parent_id__isnull=True) | Q(parent__status__state__exact=GESPLITST)
                )  # SIG-2931, special case for children of split signal
            }
        },
        'kwargs': {
            'subject': 'Betreft melding: {signal_id}',
            'templates': {
                'txt': 'email/signal_status_changed_heropend.txt',
                'html': 'email/signal_status_changed_heropend.html'
            }
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
                    GEMELD,  # no need for extra filtering, send_mail=True is enough
                    AFWACHTING,
                    BEHANDELING,
                    ON_HOLD,
                    VERZOEK_TOT_AFHANDELING,
                    GEANNULEERD,  # TODO: do we GEANNULEERD to send emails?
                ],
                'status__send_email__exact': True,  # on create_initial this is False (model default)
            },
            'functions': {
                'no_children': lambda signal: Signal.objects.filter(id=signal.id).filter(
                    Q(parent_id__isnull=True) | Q(parent__status__state__exact=GESPLITST)
                )  # SIG-2931, special case for children of split signal
            }
        },
        'kwargs': {
            'subject': 'Meer over uw melding {signal_id}',
            'templates': {
                'txt': 'email/signal_status_changed_optional.txt',
                'html': 'email/signal_status_changed_optional.html',
            },
            'context': lambda signal: dict(afhandelings_text=signal.status.text)
        }
    }
]


def _create_feedback_and_mail_context(signal: Signal):
    """
    Util functions to create the feedback object and create the context needed for the mail

    :param signal:
    :return:
    """
    from signals.apps.feedback.models import Feedback
    from signals.apps.feedback.utils import get_feedback_urls

    feedback = Feedback.actions.request_feedback(signal)
    positive_feedback_url, negative_feedback_url = get_feedback_urls(feedback)
    return {
        'negative_feedback_url': negative_feedback_url,
        'positive_feedback_url': positive_feedback_url,
    }


class MailActions:
    _from_email = settings.NOREPLY

    def __init__(self, mail_rules=SIGNAL_MAIL_RULES) -> None:
        self._conditions = {}
        self._kwargs = {}

        for config in mail_rules:
            key = slugify(config['name'])

            self._conditions[key] = config['conditions']
            self._kwargs[key] = config['kwargs'] or {}

    def _apply_filters(self, filters: dict, signal: Signal) -> bool:
        try:
            Signal.objects.filter(**filters).get(pk=signal.pk)
            return True
        except Signal.DoesNotExist:
            pass
        return False

    def _apply_functions(self, functions: dict, signal: Signal) -> bool:
        return all([
            function(signal)
            for _, function in functions.items()
        ])

    def _apply_conditions(self, conditions: dict, signal: Signal) -> Any:
        filters = conditions['filters'] if 'filters' in conditions else {}
        functions = conditions['functions'] if 'functions' in conditions else {}

        return (self._apply_filters(filters=filters, signal=signal) and
                self._apply_functions(functions=functions, signal=signal))

    def _get_actions(self, signal: Signal) -> list:
        found_actions_to_apply = []
        for key, conditions in self._conditions.items():
            if self._apply_conditions(conditions=conditions, signal=signal):
                found_actions_to_apply.append(key)
        return found_actions_to_apply

    def _get_mail_context(self, signal: Signal, mail_kwargs: dict):
        context = {'signal': signal, 'status': signal.status}

        if 'context' in mail_kwargs and callable(mail_kwargs['context']):
            context.update(mail_kwargs['context'](signal))
        elif 'context' in mail_kwargs and isinstance(mail_kwargs['context'], dict):
            context.update(mail_kwargs['context'])

        return context

    def _mail(self, signal: Signal, mail_kwargs: dict):
        context = self._get_mail_context(signal=signal, mail_kwargs=mail_kwargs)

        message = loader.get_template(mail_kwargs['templates']['txt']).render(context)
        html_message = loader.get_template(mail_kwargs['templates']['html']).render(context)
        subject = mail_kwargs['subject'].format(signal_id=signal.id)

        return django_send_mail(subject=subject, message=message, from_email=self._from_email,
                                recipient_list=[signal.reporter.email, ], html_message=html_message)

    def apply(self, signal_id: int, send_mail: bool = True) -> None:
        signal = Signal.objects.get(pk=signal_id)

        actions = self._get_actions(signal=signal)
        for action in actions:
            kwargs = copy.deepcopy(self._kwargs[action])

            if send_mail:
                self._mail(signal=signal, mail_kwargs=kwargs)
