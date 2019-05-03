"""
Bulk re-categorization
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

# -- relevant API endpoints --
DETAIL_ENDPOINT = '{base_url}/signals/v1/private/signals/{signal_id}'

# -- relevant message payloads (use as templates) --
UPDATE_CATEGORY = {
    'category': {
        'sub_category': 'CATEGORY_URL_PLACEHOLDER',  # update when SIG-1029 is fixed
        'text': 'MESSAGE_PLACEHOLDER'
    }
}

MESSAGE = 'Omdat er nieuwe categorieën zijn ingevoerd in SIA is deze melding overnieuw ingedeeld.'


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

    def _check_category(self, signal_id):
        pass

    def get_list_for_category(self, category_url):
        pass

    def update_category(self, signal_id, new_state, message):
        pass


class BulkCategoryAssignment():
    def __init__(self, api_client, old_cat, new_cat, message):
        self.api_client = api_client
        self.old_cat = old_cat
        self.new_cat = new_cat
        self.message = message

    def run(self, n_retries):
        pass


def handle_env():
    """Grab SIA user email and password from the relevant environment variables."""
    class NameSpace():
        pass

    email = os.getenv('SIA_EMAIL')  # SIA usernames are always email addresses
    password = os.getenv('SIA_PASSWORD')

    if email is None or password is None:
        raise EnvironmentError('Either or both of SIA_USERNAME and SIA_PASSWORD not set.')

    ns = NameSpace()
    ns.email = email
    ns.password = password

    return ns


def handle_cli():
    """Handle command line arguments, check them."""

    def is_known_env(value):
        """Check whether environment is known, return environment if known else ValueError."""
        if value not in ['dev', 'acc', 'prod']:
            raise ValueError(f'Unknown environment {value}')
        return value

    def category_url_is_relative(value):
        """Category URL should be relative path."""
        # TODO: validate that we have a category_url like path (without host and port)
        #       raise relevant ValueError if not.
        raise NotImplementedError('URL check not implemented yet.')
        return value

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'old', type=category_url_is_relative, help='Category from which to reassign (as URL path).'
    )
    parser.add_argument(
        'new', type=category_url_is_relative, help='Category to which to reassign (as URL path).'
    )
    parser.add_argument(
        'env', type=is_known_env, help='One of "dev", "prod" or "acc" (without double quotes)'
    )

    return parser.parse_args()


def main():
    args = handle_cli()
    env = handle_env()

    base_url = 'http://127.0.0.1:8000'
    if args.env == 'acc':
        base_url = 'https://acc.api.data.amsterdam.nl'
    elif args.env == 'prod':
        base_url = 'https://api.data.amsterdam.nl'

    api_client = APIClient(base_url, env.email, env.password, args.env)

    bulk_task = BulkCategoryAssignment(
        api_client,
        args.old,
        args.new,
        MESSAGE  # hardcoded for now
    )
    bulk_task.run()

if __name__ == '__main__':
    main()