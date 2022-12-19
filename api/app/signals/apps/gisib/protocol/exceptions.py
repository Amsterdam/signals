# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam


class GISIBException(Exception):
    pass


class GISIBLoginFailed(GISIBException):
    pass
