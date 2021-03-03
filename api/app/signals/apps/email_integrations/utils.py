from signals.apps.feedback.models import Feedback
from signals.apps.feedback.utils import get_feedback_urls
from signals.apps.signals.models import Signal


def _create_feedback_and_mail_context(signal: Signal):
    """
    Util functions to create the feedback object and create the context needed for the mail
    """
    feedback = Feedback.actions.request_feedback(signal)
    positive_feedback_url, negative_feedback_url = get_feedback_urls(feedback)
    return {
        'negative_feedback_url': negative_feedback_url,
        'positive_feedback_url': positive_feedback_url,
    }
