# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from signals.apps.signals.factories import SignalDepartmentsFactory


class DirectingDepartmentsFactory(SignalDepartmentsFactory):
    relation_type = 'directing'
