from django.conf import settings
from rest_framework.reverse import reverse


def get_feedback_urls(feedback):
    """Get positive and negative feedback URLs in meldingingen application."""
    # Note: this task is not running in the request-response cycle. We cannot
    # grab the scheme and host from current request, hence:
    host = settings.SITE_DOMAIN
    scheme = 'https' if 'localhost' not in host else 'http'

    feedback_url = reverse('v1:feedback-forms-detail', kwargs={'pk': feedback.uuid})
    positive_feedback_url = f'{scheme}://{host}{feedback_url}?is_satisfied=true'
    negative_feedback_url = f'{scheme}://{host}{feedback_url}?is_satisfied=false'
    assert 'http' in positive_feedback_url, positive_feedback_url

    return positive_feedback_url, negative_feedback_url
