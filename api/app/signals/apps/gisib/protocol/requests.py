# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from datetime import date
from typing import Optional

import requests
from requests import HTTPError

from signals.apps.gisib import app_settings
from signals.apps.gisib.protocol.exceptions import GISIBException, GISIBLoginFailed
from signals.apps.gisib.protocol.filters import Filters


class GISIBLoginRequest:
    endpoint = f'{app_settings.GISIB_ENDPOINT}/Login'

    def __call__(self) -> Optional[str]:
        return self.post()

    def post(self) -> Optional[str]:
        response = requests.post(self.endpoint, json={
            'Username': app_settings.GISIB_USERNAME,
            'Password': app_settings.GISIB_PASSWORD,
            'ApiKey': app_settings.GISIB_APIKEY,
        })

        if response.status_code == 200:
            return response.text
        elif response.status_code in [400, 401]:
            raise GISIBLoginFailed()
        else:
            raise GISIBException()


class GISIBCollectionWithFilterRequest:
    login_request = GISIBLoginRequest()

    def __init__(self, bearer_token: str = None):
        self.bearer_token = bearer_token if bearer_token else self.login_request()

    @property
    def _request_headers(self):
        return {'Authorization': f'Bearer {self.bearer_token}'}

    def __call__(self, object_kind_name: str, filters: Filters, offset: int = 0,
                 limit: int = app_settings.GISIB_LIMIT) -> Optional[dict]:
        return self.post(object_kind_name, filters, offset, limit)

    def post(self, object_kind_name: str, filters: Filters, offset: int = 0,
             limit: int = app_settings.GISIB_LIMIT) -> Optional[dict]:
        endpoint = f'{app_settings.GISIB_ENDPOINT}/Collections/{object_kind_name}/WithFilter/Items'
        query_params = {'offset': offset, 'limit': limit}
        response = requests.post(endpoint, params=query_params, json=filters.as_list(), headers=self._request_headers)

        try:
            response.raise_for_status()
        except HTTPError as e:
            raise GISIBException(str(e))
        else:
            return response.json()


class GISIBCollectionDeletedItemsRequest:
    login_request = GISIBLoginRequest()

    def __init__(self, bearer_token: str = None):
        self.bearer_token = bearer_token if bearer_token else self.login_request()

    @property
    def _request_headers(self):
        return {'Authorization': f'Bearer {self.bearer_token}'}

    def __call__(self, object_kind_name: str, reference_date: date) -> Optional[dict]:
        return self.get(object_kind_name, reference_date)

    def get(self, object_kind_name: str, reference_date: date) -> Optional[dict]:
        endpoint = f'{app_settings.GISIB_ENDPOINT}/Collections/{object_kind_name}/DeletedItems'
        query_params = {'referenceDate': reference_date.strftime('%Y/%m/%d')}
        response = requests.get(endpoint, params=query_params, headers=self._request_headers)

        try:
            response.raise_for_status()
        except HTTPError as e:
            raise GISIBException(str(e))
        else:
            return response.json()
