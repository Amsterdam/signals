"""
Bulk cancellation of signals based on CSV of signal ids.

Script is idempotent.
"""
import csv
import json
import os
from urllib.parse import urlencode

import requests
from requests.exceptions import RequestException

from get_signals import GetAccessToken

N_RETRIES = 5

# -- relevant API endpoints --
DETAIL_ENDPOINT = '{base_url}/signals/v1/private/signals/{signal_id}'

# -- relevant message payloads (use as templates) --
UPDATE_STATUS = {
    'status': {
        'state': 'STATE_PLACEHOLDER',
        'text': 'MESSAGE_PLACEHOLDER',
    }
}


class APIClient():
    def __init__(self, base_url, email, password, environment):
        self.headers = self._get_auth_header(email, password, environment)

    def _get_auth_header(self, email, password, environment):
        return {}  # first for local updates, implement token requests later.

    def _check_status(signal_id):
        response = requests.get(
            DETAIL_ENDPOINT.format(self.base_url, signal_id),
            headers=self.headers
        )
        response.raise_for_status()

        json_data = response.json()
        return status

    def update_status(signal_id, new_state, message):
        # check status
        current_status = self._check_status(signal_id)
        if current_status.state == new_state:
            return  # already in desired state

        # mutate signal status
        payload = copy.deepcopy{UPDATE_STATUS}
        payload['status']['state'] = new_state
        payload['status']['text'] = message

        response = requests.patch(
            DETAIL_ENDPOINT.format(self.base_url, signal_id),
            data=payload,
            headers=self.headers,
            format='json'
        )
        response.raise_for_status()


class BulkCancellation():
    def __init__(self, api_client, filename, message):
        # Note expects authenticated APIClient instance
        self.api_client = api_client

        self.to_process = set(self._parse_csv(filename))
        self.processed = set()

        self.message = message

    def _parse_csv(self, filename):
        """Parse CSV with signal_ids to update."""
        signal_ids = []
        with open(filename, 'r') as f:
            reader = csv.reader(f)

            for row in reader:
                try:
                    id_ = int(row[0])
                except (ValueError, IndexError) as e:
                    pass
                else:
                    signal_ids.append(id_)
        return signal_ids

    def _perform_updates(self):
        """Loop through all signals to cancel, and try to cancel them once."""
        failed = set()
        succeeded = set()

        for signal_id in signal_ids:
            try:
                self.api_client.update_status(signal_id, GEANNULEERD, self.message)
            except RequestException:
                print(f'Failed to process {signal_id}.')
                failed.add(signal_id)
            else:
                succeeded.add(signal_id)

        self.to_process = self.to_process - succeeded
        self.processed = self.processed | succeeded


    def handle(self, n_retries=5):
        for i in range(n_retries):
            if not self.to_process:
                break

            self._perform_updates()



if __name__ == '__main__':
    access_token = {}
    environment = os.getenv('SIGNALS_ENVIRONMENT', 'dev')

    if environment.lower() in ['acc', 'prod']:
        email = os.getenv('SIGNALS_USER', 'signals.admin@example.com')
        password = os.getenv('SIGNALS_PASSWORD', 'insecure')

        access_token = GetAccessToken().getAccessToken(email, password, environment)
        print(f'Received new Access Token Header: {access_token}')

    if access_token or environment.lower() == 'dev':
        action = UpdateCategory(access_token, environment)

        old_category = os.getenv('CATEGORY')
        new_category_slug = os.getenv('NEW_CATEGORY_SLUG')

        if old_category and new_category_slug:
            action.handle(old_category, new_category_slug)
        else:
            print('No category and new category set')