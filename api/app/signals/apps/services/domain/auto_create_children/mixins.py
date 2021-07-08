# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
class ExtraPropertiesMixin:
    def get_extra_properties(self, signal, extra_property_id):
        if not signal.extra_properties:
            return []

        containers = {}
        for extra_property in signal.extra_properties:
            if extra_property.get('id', '').lower() == extra_property_id:
                for container in extra_property['answer']:
                    containers[str(container['id']).lower()] = container

        return containers.values()
