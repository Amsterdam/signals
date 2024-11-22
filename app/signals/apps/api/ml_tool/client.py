# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2024 Gemeente Amsterdam
import requests
from django.conf import settings
from django.core import validators
from requests import ConnectTimeout

from signals.apps.api.generics.exceptions import GatewayTimeoutException


class MLToolClient:
    timeout = (10.0, 10.0)
    endpoint = '{}/predict'.format(settings.ML_TOOL_ENDPOINT)
    predict_validators = [
        validators.MinLengthValidator(limit_value=1),
    ]

    def predict(self, text):
        for validator in self.predict_validators:
            validator(text)

        try:
            response = requests.post(self.endpoint, json={'text': text}, timeout=self.timeout)
        except (ConnectTimeout, ):
            raise GatewayTimeoutException()
        else:
            return response
