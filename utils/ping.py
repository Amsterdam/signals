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


AUTH_ME_ENDPOINT = '{base_url}/signals/auth/me/'  # still V0, fix this

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
    
    def ping(self):
        """Check whether the API allows an authenticated request for this user."""

        response = requests.get(
            AUTH_ME_ENDPOINT.format(base_url=self.base_url),
            headers=self.headers
        )

        return response.status_code == 200


def handle_cli():
    def is_known_env(value):
        """Check whether environment is known, return environment if known else ValueError."""
        if value not in ['dev', 'acc', 'prod']:
            raise ValueError(f'Unknown environment {value}')
        return value

    parser = argparse.ArgumentParser(
        description='Ping SIA, check that user can log in.',
        epilog='SIA_EMAIL and SIA_PASSWORD must be set in environment.'
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
    is_authenticated = api_client.ping()

    if is_authenticated:
        print('User {} is successfully authorized for SIA.'.format(env.email))
    else:
        print('User {} is not authorized for SIA'.format(env.email))

if __name__ == '__main__':
    main()
