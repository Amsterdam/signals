"""
How to run the script

    export PYTHONPATH=.
    export SIGNALS_ENVIRONMENT={CHOICE: dev,acc,prod}
    export SIGNALS_USER=signals.admin@example.com
    export SIGNALS_PASSWORD=insecure
    export CATEGORY={THE OLD CATEGORY THAT NEEDS TO BE REPLACED}
    export NEW_CATEGORY_SLUG={THE NEW CATEGORY THAT NEEDS TO REPLACE THE CATEGORY FQDN}
    python update_category.py

"""

import json
import os
from time import sleep
from urllib.parse import urlencode

import requests

from get_signals import GetAccessToken

MESSAGE = 'Omdat er nieuwe categorieën zijn ingevoerd in SIA is deze melding overnieuw ingedeeld.'
DELAY = 0.1

class UpdateCategory:
    def __init__(self, headers, environment):
        self.success = 0
        self.errors = []

        self.headers = headers
        self.headers['content-type'] = 'application/json'

        self.environment = environment

        print('Environment: {}'.format(environment))
        if environment.lower() == 'dev':
            self.url = 'http://127.0.0.1:8000/signals'
        elif environment.lower() == 'acc':
            self.url = 'https://acc.api.data.amsterdam.nl/signals'
        elif environment.lower() == 'prod':
            self.url = 'https://api.data.amsterdam.nl/signals'
        print('URL: {}'.format(self.url))

    def _filter_by_category(self, category):
        query_params = urlencode({'category_slug': category})
        endpoint = '{url}/v1/private/signals/?{query_params}'.format(url=self.url,
                                                                     query_params=query_params)
        print(endpoint)
        r = requests.get(endpoint, headers=self.headers)
        if r.status_code == 200:
            data = r.json()

            print('Total Signals to change: {}'.format(data['count']))

            return data['results']

    def _update_category(self, signal_id, new_category_slug):
        endpoint = '{url}/v1/private/signals/{signal_id}'.format(url=self.url, signal_id=signal_id)
        data = json.dumps({
            'category': {
                'sub_category': new_category_slug,
                'text': MESSAGE,
            }
        })

        r = requests.patch(endpoint, data=data, headers=self.headers)
        if r.status_code == 200:
            print('Updated category for Signal #{}'.format(signal_id))
            self.success += 1
        else:
            print('Failed to update the category for Signal #{}'.format(signal_id))
            self.errors.append(signal_id)

    def _loop(self, old_category, new_category_slug):
        results = self._filter_by_category(old_category)
        if not results:
            return

        for signal in results:
            if signal['id'] not in self.errors:
                sleep(DELAY)
                self._update_category(signal_id=signal['id'], new_category_slug=new_category_slug)
        self._loop(old_category, new_category_slug)

    def handle(self, old_category, new_category_slug):
        # Reset the counters
        self.success = 0
        self.errors = []

        self._loop(old_category, '{}{}'.format(self.url, new_category_slug))

        print('----------------------------------------')

        if self.success:
            print('Succesfully changed: {}'.format(self.success))

        if self.errors:
            print('Errors: {}'.format(len(self.errors)))
            print('Signals that have failed: {}'.format(', '.join(self.errors)))

        print('Done!')


if __name__ == "__main__":
    access_token = {}
    environment = os.getenv('SIGNALS_ENVIRONMENT', 'dev')

    if environment.lower() in ['acc', 'prod']:
        email = os.getenv('SIGNALS_USER', 'signals.admin@example.com')
        password = os.getenv('SIGNALS_PASSWORD', 'insecure')

        acceptance = True if environment.lower() == 'acc' else False
        access_token = GetAccessToken().getAccessToken(email, password, acceptance)
        print(f'Received new Access Token Header: {access_token}')

    if access_token or environment.lower() == 'dev':
        action = UpdateCategory(access_token, environment)

        old_category = os.getenv('CATEGORY')
        new_category_slug = os.getenv('NEW_CATEGORY_SLUG')

        if old_category and new_category_slug:
            action.handle(old_category, new_category_slug)
        else:
            print('No category and new category set')
