# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam

class URLEncodedCharsFoundInText(Exception):
    """
    Exception to be raised when a URL encoded character is found in a text
    """
    pass
