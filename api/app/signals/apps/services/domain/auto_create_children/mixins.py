# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
class BaseExtraPropertiesMixin:
    def _get_extra_properties(self, signal, extra_property_id):
        if not signal.extra_properties:
            return []

        containers = {}
        for extra_property in signal.extra_properties:
            if extra_property.get('id', '').lower() == extra_property_id:
                for container in extra_property['answer']:
                    containers[str(container['id']).lower()] = container

        return containers.values()


class ContainerExtraPropertiesMixin(BaseExtraPropertiesMixin):
    def get_extra_properties(self, signal):
        """
        Example of container data in the extra_properties of a Signal:

        "extra_properties": [
            {
                "id": "extra_container",
                "label": "Container(s)",
                "answer": [
                    {
                        "id": "REK00853",
                        "type": "Rest",
                        "description": "Restafval container"
                    }
                ],
                "category_url": "/signals/v1/public/terms/categories/afval/sub_categories/container-is-vol"
            }
        ]
        """
        return self._get_extra_properties(signal, 'extra_container')


class EikenprocessierupsExtraPropertiesMixin(BaseExtraPropertiesMixin):
    def get_extra_properties(self, signal):
        """
        Example of container data in the extra_properties of a Signal:

        "extra_properties": [
            {
                "id": "extra_eikenprocessierups",
                "label": "Boom",
                "answer": [
                    {
                        "id": 317744,
                        "type": "Eikenboom",
                        "GlobalID": "69f65d5d-f0a7-4b9a-a23b-8e04077a0b91",
                        "isReported": false,
                        "description": "Eikenboom"
                    }
                ],
                "category_url": "/signals/v1/public/terms/categories/openbaar-groen-en-water/sub_categories/eikenprocessierups"
            }
        ]
        """  # noqa
        return self._get_extra_properties(signal, 'extra_eikenprocessierups')
