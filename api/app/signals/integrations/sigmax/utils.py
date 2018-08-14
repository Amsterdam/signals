import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def _format_datetime(dt: datetime) -> str:
    """Format datetime as YYYYMMDDHHMMSS."""
    return dt.strftime('%Y%m%d%H%M%S')


def _format_date(dt: datetime) -> str:
    """Format date as YYYYMMDD."""
    return dt.strftime('%Y%m%d')


def _get_session_with_retries() -> requests.Session:
    """
    There can be a some delays in processing from Sigmax. This retry logic
    handles most of that without having to reschedule the task. If this fails
    normal celery retry logic wil be applied.

    Get a requests Session that will retry 5 times
    on a number of HTTP 500 statusses.
    """
    session = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=True
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    return session
