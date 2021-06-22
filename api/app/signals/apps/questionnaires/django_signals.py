# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.dispatch import Signal as DjangoSignal

session_frozen = DjangoSignal()
