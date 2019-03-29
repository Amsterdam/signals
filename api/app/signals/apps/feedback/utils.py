import copy
import logging
import os

from django.conf import settings

from signals.apps.feedback import app_settings as feedback_settings

logger = logging.getLogger(__name__)


class NoFrontendAppConfigured(Exception):
    pass


def get_fe_application_location():
    """Get location of frontend SIA application."""
    env_fe_mapping = copy.deepcopy(getattr(
        settings,
        'FEEDBACK_ENV_FE_MAPPING',
        feedback_settings.FEEDBACK_ENV_FE_MAPPING
    ))

    environment = os.getenv('ENVIRONMENT', None)

    try:
        environment = environment.upper()
        fe_location = env_fe_mapping[environment]
    except (AttributeError, KeyError) as e:  # noqa: F841
        msg = f'ENVIRONMENT environment variable set to unknown value: {environment}'
        raise NoFrontendAppConfigured(msg)
    else:
        return fe_location


def get_feedback_urls(feedback):
    """Get positive and negative feedback URLs in meldingingen application."""
    try:
        fe_location = get_fe_application_location()
    except NoFrontendAppConfigured:
        return 'http://dummy_link/kto/yes/123', 'http://dummy_link/kto/no/123'

    positive_feedback_url = f'{fe_location}/kto/ja/{feedback.token}'
    negative_feedback_url = f'{fe_location}/kto/nee/{feedback.token}'

    return positive_feedback_url, negative_feedback_url
