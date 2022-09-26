import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def create_session_for_external_reaction_request(signal):
    # HIERZO!!!
    pass


def get_external_reaction_url(session):
    return f'{settings.FRONTEND_URL}/incident/externe_reactie/{session.uuid}'
