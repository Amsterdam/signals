# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
import json
import requests
import os


class GetAccessToken:
    def getAccessToken(self, client_id, client_secret, acceptance=True):
        environment = 'acc' if acceptance else 'b'
        response = requests.post(
            f'https://iam.amsterdam.nl/auth/realms/datapunt-ad-{environment}/protocol/openid-connect/token',
            data={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
            }
        )
        if response.status_code == 200:
            return {
                'Authorization': f'Bearer {response.json()["access_token"]}',
            }


if __name__ == "__main__":
    access_token_header = GetAccessToken().getAccessToken(
        client_id=os.getenv('SIGNALS_USER', 'signals.admin@example.com'),
        client_secret=os.getenv('SIGNALS_PASSWORD', 'insecure'),
    )

    if access_token_header:
        print(f'Received Access Token Header: {access_token_header["Authorization"]}')

        response = requests.get(
            'https://acc.api.data.amsterdam.nl/signals/v1/private/signals?page_size=5',
            headers=access_token_header
        )
        print(json.dumps(response.json(), indent=4))
