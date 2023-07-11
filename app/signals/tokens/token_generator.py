# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from secrets import token_urlsafe


class TokenGenerator:
    """This class should be used whenever a secure token of some sort needs
    to be generated within the application.
    """

    def __call__(self) -> str:
        """Generate a secure token.

        Returns
        -------
        str
            The generated secure token.
        """
        return token_urlsafe()
