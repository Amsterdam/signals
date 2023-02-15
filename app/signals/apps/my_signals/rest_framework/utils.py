# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
class AuthenticatedReporter:
    """
    Util class to populate the user on the request
    """
    def __init__(self, email=None):
        self.email = email

    def is_authenticated(self):
        return bool(self.email)

    def is_anonymous(self):
        return not bool(self.email)
