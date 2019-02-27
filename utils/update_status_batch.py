"""
Batch updater, reads CSV, uses SIA V1 API to update Signals in SIA.

Rationale for using the API:
The SIA API will log all actions and attribute them to a user. By using the API
for bulk updates everything will be logged correctly. Furthermore, there should
be one well maintained and complete interface to the data: the API.
"""
import csv

import requests

# Modes:
# - local development: no log-in
# - acceptation: logged-in
# - production: logged-in

# - should be resuamable without re-doing changes

class CSVValidationError(Exception):
    pass


class AlreadyUpdated(Exception):
    pass


class StatusUpdater:
    DETAIL_PATH = '/v1/private/signals/{signal_id}'
    DELIMITER = ';'

    def __init__(self, csv_file, base_url, email, password):
        """Load CSV file with requested updates plus some sanity checks."""
        self._rows = self._load_csv(csv_file)
        self._authorization_header = self._get_authorization_header()

    def _load_csv(self, csv_file):
        """Load CSV file and perform some sanity checks."""
        rows = []
        with open(csv_file, 'r') as f:
            reader = csv.reader(f, delimiter=self.DELIMITER)

            for i, row in enumerate(reader(), start=1):
                if len(row) != 3:
                    raise CSVValidationError(
                        'Error in line {}. It should contain 3 fields. '
                        'Current line contains: {}'.format(i , row)
                    )
                try:
                    int(row[0])
                except ValueError:
                    raise CSVValidationError(
                        'Error in CSV file line {}. '
                        'First column must contain numerical signal id. '
                        'This field currently contains {}'.format(i, row[0])
                    )
                # TODO: once eligable statusses are exposed in API, check that
                # requested status change is possible.
                rows.append(row)

        return rows

    def _get_authorization_header(self):
        pass

    def _get_signal(self, signal_id):
        pass

    def _patch_signal(self, signal_id, status, message):
        pass

    def _process_row(self, row):
        """Update a single Signal."""
        signal_id, target_status, target_msg = row

        signal_data = self._get_signal(signal_id)   ## Move to requests, see etags
        if signal_data['status']['state'] == target_status and \
                signal_data['status']['text'] == target_msg:
            error_msg = 'Signal {} was already updated.'.format(signal_id)
            raise AlreadyUpdated(error_msg)

        self._patch_signal(signal_id, target_status, target_msg)

    def _process_rows(self):
        """Update all Signals as requested in CSV file."""

        for i, row in enumerate(self._rows, start=1):
            try:
                self._process_row(row)
            except AlreadyUpdated:
                print('Already processed line {}, skipping'.format(i))
            # TODO: HTTP STATUS CODE ERRORS THAT BUBBLE UP FROM self._patch_signal

    def run(self):
        self._process_rows()

