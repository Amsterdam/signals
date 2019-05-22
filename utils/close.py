"""
Bulk cancellation of signals based on CSV of signal ids.

Script is idempotent.
"""
import argparse
import csv
import copy
import json
import os
import time
import traceback
from urllib.parse import urlencode

import requests
from requests.exceptions import RequestException

from get_signals import GetAccessToken

N_RETRIES = 5
SLEEP_DELAY = 0.1
GEANNULEERD = 'a'
AFGEHANDELD = 'o'

# -- relevant API endpoints --
DETAIL_ENDPOINT = '{base_url}/signals/v1/private/signals/{signal_id}'

# -- relevant message payloads (use as templates) --
UPDATE_STATUS = {
    'status': {
        'state': 'STATE_PLACEHOLDER',
        'text': 'MESSAGE_PLACEHOLDER',
    }
}

MESSAGE = 'Dit betreft een melding die handmatig is overgenomen in Techview ' \
'en daar is afgehandeld, inclusief afmeldbericht naar de melder. Deze ' \
'melding is daarom in SIA geannuleerd.'


class APIClient():
    def __init__(self, base_url, email, password, environment):
        self.headers = self._get_auth_header(email, password, environment)
        self.base_url = base_url

    def _get_auth_header(self, email, password, environment):
        # TODO: refactor the login script (get_signals.py)
        if environment == 'dev':
            return {}
        elif environment in ['acc', 'prod']:
            print('Retrieving access token via OAuth2')
            acceptance = environment == 'acc'
            headers = GetAccessToken().getAccessToken(email, password, acceptance)
            assert headers, 'We need to get Authorization headers, but did not.'
            return headers
        else:
            raise ValueError(f'Unknown environment {environment}')

    def _check_status(self, signal_id):
        response = requests.get(
            DETAIL_ENDPOINT.format(base_url=self.base_url, signal_id=signal_id),
            headers=self.headers
        )
        response.raise_for_status()

        json_data = response.json()
        state = json_data['status']['state']
        print(f'Current state SIA-{signal_id} is {state}.')
        return json_data['status']

    def update_status(self, signal_id, new_state, message, acceptable_states=None):
        if acceptable_states is None:
            acceptable_states = []
        acceptable_states.append(new_state)  # if we are in desired state, skip

        # check status
        current_status = self._check_status(signal_id)
        if current_status['state'] in acceptable_states:
            print('Already in desired state.')
            return  # already in desired state

        # mutate signal status
        print('mutate')
        payload = copy.deepcopy(UPDATE_STATUS)
        payload['status']['state'] = new_state
        payload['status']['text'] = message

        response = requests.patch(
            DETAIL_ENDPOINT.format(base_url=self.base_url, signal_id=signal_id),
            json=payload,
            headers=self.headers,
        )
        response.raise_for_status()
        self._check_status(signal_id)
        print('')


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
        with open(filename, 'r', encoding='cp1252') as f:
            reader = csv.reader(f, delimiter=';')

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

        for signal_id in self.to_process:
            try:
                self.api_client.update_status(
                    signal_id, GEANNULEERD, self.message, [AFGEHANDELD])
            except RequestException:
                print(f'Failed to process {signal_id}.')
                failed.add(signal_id)
            else:
                succeeded.add(signal_id)
            time.sleep(SLEEP_DELAY)

        self.to_process = self.to_process - succeeded
        self.processed = self.processed | succeeded

    def run(self, n_retries=5):
        # cancel signals
        try:
            for i in range(n_retries):
                if not self.to_process:
                    break

                self._perform_updates()
        except (Exception,  KeyboardInterrupt) as e:
            print('Unhandled exception:')
            traceback.print_exc()
        finally:
            # report failures
            failed_ids = list(self.to_process)
            failed_ids.sort()
            print('-' * 40)
            print('Processed {} signals.'.format(len(self.processed)))
            print('Failed to process {} signals.'.format(len(self.to_process)))
            print('\n\nThe following signal ids could not be processed:')
            for signal_id in failed_ids:
                print(signal_id)


def handle_cli():
    def is_known_env(value):
        """Check whether environment is known, return environment if known else ValueError."""
        if value not in ['dev', 'acc', 'prod']:
            raise ValueError(f'Unknown environment {value}')
        return value

    parser = argparse.ArgumentParser(
        description='Bulk closure of signals from CSV with signal IDs.',
        epilog='SIA_EMAIL and SIA_PASSWORD must be set in environment.'
    )
    parser.add_argument(
        'csv_file', type=str, help='CSV file of SIA signal ids (without the SIA- part)'
    )
    parser.add_argument(
        'env', type=is_known_env, help='One of "dev", "prod" or "acc" (without double quotes)'
    )

    return parser.parse_args()


def handle_env():
    """Grab SIA user email and password from the relevant environment variables."""
    class NameSpace():
        pass

    email = os.getenv('SIA_USERNAME')  # SIA usernames are always email addresses !
    password = os.getenv('SIA_PASSWORD')

    if email is None or password is None:
        raise EnvironmentError('Either or both of SIA_USERNAME and SIA_PASSWORD not set.')

    ns = NameSpace()
    ns.email = email
    ns.password = password

    return ns


def main():
    args = handle_cli()
    env = handle_env()

    base_url = 'http://127.0.0.1:8000'
    if args.env == 'acc':
        base_url = 'https://acc.api.data.amsterdam.nl'
    elif args.env == 'prod':
        base_url = 'https://api.data.amsterdam.nl'

    api_client = APIClient(base_url, env.email, env.password, args.env)

    bulk_task = BulkCancellation(
        api_client,
        args.csv_file,
        MESSAGE  # hardcoded for now
    )
    bulk_task.run()

if __name__ == '__main__':
    main()