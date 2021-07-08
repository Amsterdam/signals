# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.conf import settings

from signals.apps.services.domain.auto_create_children.mixins import (
    ContainerExtraPropertiesMixin,
    EikenprocessierupsExtraPropertiesMixin
)
from signals.apps.signals.workflow import GEMELD


class ContainerRule(ContainerExtraPropertiesMixin):
    trigger_category_slugs = (
        'container-is-vol',
        'container-is-kapot',

        'container-voor-papier-is-vol',
        'container-voor-papier-is-stuk',

        'container-voor-plastic-afval-is-vol',
        'container-voor-plastic-afval-is-kapot',

        'container-glas-vol',
        'container-glas-kapot',
    )

    def __call__(self, signal):
        """
        - A signal is not a parent or a child signal
        - A signal has the status "GEMELD" ("m")
        - A signal belongs to the sub category "container-is-vol", "container-voor-papier-is-vol",
          "container-voor-plastic-afval-is-vol", "container-glas-vol", "container-glas-kapot",
          "container-is-kapot", "container-voor-papier-is-stuk", or "container-voor-plastic-afval-is-kapot".
        - A signal must contain at least 2 or more containers but not more than the value of the setting SIGNAL_MAX_NUMBER_OF_CHILDREN

        For now this is only used to create child signals when multiple containers are selected.
        """  # noqa
        if not settings.FEATURE_FLAGS.get('AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_CONTAINER', False):
            return False

        if signal.is_parent or signal.is_child or signal.status.state != GEMELD:
            return False

        category_slug = signal.category_assignment.category.slug
        if category_slug not in self.trigger_category_slugs:
            return False

        selected_containers = len(self.get_extra_properties(signal))
        if selected_containers < 2:
            return False

        if selected_containers > settings.SIGNAL_MAX_NUMBER_OF_CHILDREN:
            return False

        return True


class EikenprocessierupsRule(EikenprocessierupsExtraPropertiesMixin):
    trigger_category_slugs = (
        'eikenprocessierups',
    )

    def __call__(self, signal):
        """
        - A signal is not a parent or a child signal
        - A signal has the status "GEMELD" ("m")
        - A signal belongs to the sub category "eikenprocessierups"
        - A signal must contain at least 2 or more containers but not more than the value of the setting SIGNAL_MAX_NUMBER_OF_CHILDREN

        For now this is only used to create child signals when multiple containers are selected.
        """  # noqa
        if not settings.FEATURE_FLAGS.get('AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_EIKENPROCESSIERUPS_TREE', False):
            return False

        if signal.is_parent or signal.is_child or signal.status.state != GEMELD:
            return False

        category_slug = signal.category_assignment.category.slug
        if category_slug not in self.trigger_category_slugs:
            return False

        selected_containers = len(self.get_extra_properties(signal))
        if selected_containers < 2:
            return False

        if selected_containers > settings.SIGNAL_MAX_NUMBER_OF_CHILDREN:
            return False

        return True
