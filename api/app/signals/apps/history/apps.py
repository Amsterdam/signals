# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.apps import AppConfig


class HistoryConfig(AppConfig):
    name = 'signals.apps.history'
    verbose_name = 'History'

    def ready(self):
        import signals.apps.history.signal_receivers.create_initial  # noqa
        import signals.apps.history.signal_receivers.create_note  # noqa
        import signals.apps.history.signal_receivers.update_category_assignment  # noqa
        import signals.apps.history.signal_receivers.update_location  # noqa
        import signals.apps.history.signal_receivers.update_priority # noqa
        import signals.apps.history.signal_receivers.update_status  # noqa
        import signals.apps.history.signal_receivers.update_type  # noqa
        import signals.apps.history.signal_receivers.update_user_signal  # noqa
        import signals.apps.history.signal_receivers.update_signal_departments  # noqa
