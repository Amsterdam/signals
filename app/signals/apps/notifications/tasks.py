import logging

from signals import settings
from signals.celery import app
import requests

logger = logging.getLogger(__name__)

@app.task
def send_notification(municipality_code: str, payload: dict, signal_id: int, notification_type: str) -> None:
    if not settings.SIGNALEN_APP_BACKEND_URL:
        logger.warning("There is no SIGNALEN_APP_BACKEND_URL environment variable in the environment configured")
        return

    if not settings.SIGNALEN_APP_BACKEND_SECRET:
        logger.warning("There is no SIGNALEN_APP_BACKEND_SECRET environment variable in the environment configured")
        return

    try:
        response = requests.post(
            f"{settings.SIGNALEN_APP_BACKEND_URL}/signalen/notifications",
            json={
                "payload": payload,
                "signal_id": signal_id,
                "notification_type": notification_type,
                "municipality_code": municipality_code,
            },
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {settings.SIGNALEN_APP_BACKEND_SECRET}'
            }
        )

        response.raise_for_status()
    except Exception as e:
        logging.info(f"Sending notification for {notification_type} for SIG-{signal_id} went wrong: {e}")