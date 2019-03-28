import json
from urllib.parse import urlencode

import requests
from django.core.management import BaseCommand

from utils.get_signals import GetAccessToken


class Command(BaseCommand):
    """
    Category from -> to

    Will update the category assignment for all Signals attached to the "from" category
    """

    url = None
    access_token = None
    production = False
    options = None

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Username')
        parser.add_argument('password', type=str, help='Password')

        parser.add_argument('from_category', type=str, help='The from category')

        parser.add_argument('to_main_category', type=str, help='The to main category')
        parser.add_argument('to_sub_category', type=str, help='The to sub category')

        parser.add_argument('--production', default=False, type=bool,
                            help='Run against the production environment')

    def handle(self, *args, **options):
        self.options = options

        if self.options['production']:
            self.stdout.write('!!! RUNNING WITH PRODUCTION SETTINGS !!!')

        self.production = True if not self.options['production'] else False

        prefix = 'acc.' if not self.production else ''
        self.url = 'https://{prefix}api.data.amsterdam.nl/signals'.format(prefix=prefix)

        self._get_access_token(self.options['email'], self.options['password'])
        self._handle(self.options['from_category'],
                     self.options['to_main_category'],
                     self.options['to_sub_category'])

    def _get_access_token(self, email, password):
        acceptance = False if self.production else True
        token = GetAccessToken().getAccessToken(email, password, acceptance)
        self.access_token = token['Authorization']

    def _get_headers(self):
        return {
            'Authorization': self.access_token,
            'content-type': 'application/json',
        }

    def _get_signals_filter_by_category(self, category):
        query_params = urlencode({'category_slug': category})
        endpoint = '{url}/v1/private/signals/?{query_params}'.format(url=self.url,
                                                                     query_params=query_params)

        response = requests.get(endpoint, headers=self._get_headers())
        response_json = response.json()
        if response.status_code == 200 and 'results' in response_json:
            return response_json['results'] if response_json['count'] > 0 else []
        else:
            self.stderr.write(json.dumps(response_json))

    def _update_signal_to_category(self, signal_id, main_category_slug, sub_category_slug):
        endpoint = '{url}/v1/private/signals/{signal_id}'.format(url=self.url, signal_id=signal_id)

        category = '{url}/v1/public/terms/categories/{main_slug}/sub_categories/{sub_slug}'.format(
            url=self.url,
            main_slug=main_category_slug,
            sub_slug=sub_category_slug,
        )

        data = json.dumps({
            'category': {
                'sub_category': category
            }
        })

        response = requests.patch(endpoint, data=data, headers=self._get_headers())
        if response.status_code == 200:
            self.stdout.write('- Assigned the new category to signal #{}'.format(signal_id))
        else:
            response_json = response.json()
            self.stderr.write('- Assigning the new category to signal #{} failed: {}'.format(
                signal_id,
                response_json['detail']
            ))

    def _handle(self, from_category, main_category_slug, sub_category_slug):
        results = self._get_signals_filter_by_category(category=from_category)
        if results:
            for signal in results:
                self._update_signal_to_category(signal_id=signal['id'],
                                                main_category_slug=main_category_slug,
                                                sub_category_slug=sub_category_slug)

            # Loop till we updated the categories for all Signals in the from_category
            self._handle(from_category, main_category_slug, sub_category_slug)

        self.stdout.write('Done!!!')
