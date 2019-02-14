import csv
import os
import sys

import requests
from get_signals import GetAccessToken

"""
update_status_batch.py - Batch update signal status script

Expects a CSV file with status updates as input, with three values per row; the signal id, the new
status (m, o, e, i, or ...) and the status change text.
"""

EMAIL = ''
PASSWORD = ''
ACCEPTANCE = True
API_URL = 'http://localhost:8000/signals'


class BatchUpdate:
    CSV_DELIMITER = ';'

    rows = []
    auth_header = {}

    success = []
    error = []

    def __init__(self, filename: str):
        with open(os.path.join(os.path.dirname(__file__), filename)) as f:
            self.rows = list(csv.reader(f, delimiter=self.CSV_DELIMITER))

        self.auth_header = self._get_access_token()

    def run(self):
        for id, status, text in self.rows:
            self._update_status(id, status, text)

    def _get_access_token(self):
        gat = GetAccessToken()
        return gat.getAccessToken(EMAIL, PASSWORD, ACCEPTANCE)

    def _update_status(self, signal_id, signal_status, update_text):
        url = API_URL + '/v1/private/signals/{}'.format(signal_id)

        resp = requests.get(url, headers=self.auth_header)

        if resp.status_code != 200:
            print("Signal {: >8}: Problem retrieving (HTTP response code {})".format(signal_id,
                                                                                     resp.status_code))
            return

        if resp.json()["status"]["state"] == signal_status:
            print("Signal {: >8}: Signal already has status '{}'".format(signal_id, signal_status))
            return

        data = {
            "status": {
                "state": signal_status,
                "text": update_text
            }
        }

        resp = requests.patch(url, json=data, headers=self.auth_header)

        if resp.status_code == 200:
            print("Signal {: >8}: Updated to status '{}' with text '{}'".format(
                signal_id,
                signal_status,
                update_text,
            ))

            return

        print("Signal {: >8}: ERROR".format(signal_id))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please provide an input CSV")
        exit(1)

    batch_update = BatchUpdate(sys.argv[1])
    batch_update.run()
