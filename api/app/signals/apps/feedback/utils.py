import os

from django.conf import settings


class NoFrontendApp(Exception):
    pass


def get_fe_application_location():
    """Get location of frontend SIA application."""
    environment = os.getenv('ENVIRONMENT', None)

    if 'localhost' in settings.SITE_DOMAIN:
        raise NoFrontendApp('In testing or development we are not running SIA frontend.')

    if environment == 'ACCEPTANCE':
        return 'https://acc.meldingen.amsterdam.nl'
    elif environment == 'PRODUCTION':
        return 'https://meldingen.amsterdam.nl'
    else:
        raise NoFrontendApp(f'ENVIRONMENT variable set to unknown value: {environment}')


def get_feedback_urls(feedback):
    """Get positive and negative feedback URLs in meldingingen application."""
    try:
        fe_location = get_fe_application_location()
    except NoFrontendApp:
        return 'http://dummy_link/kto/yes/123', 'http://dummy_link/kto/no/123'

    positive_feedback_url = f'{fe_location}/kto/ja/{feedback.token}'
    negative_feedback_url = f'{fe_location}/kto/nee/{feedback.token}'

    return positive_feedback_url, negative_feedback_url
