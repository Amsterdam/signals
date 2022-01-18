# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from signals.settings.testing import *  # noqa

DATABASES['default']['HOST'] = 'localhost'  # noqa: F405
