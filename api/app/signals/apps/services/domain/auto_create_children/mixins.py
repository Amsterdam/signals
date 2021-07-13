# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
class ExtraPropertiesMixin:
    def get_assets(self, signal, extra_property_id):
        """
        Extract asset data (e.g. selected containers) from extra_properties.
        """
        if not signal.extra_properties:
            return []

        assets = {}
        for extra_property in signal.extra_properties:
            if extra_property.get('id', '').lower() == extra_property_id:
                for asset in extra_property['answer']:
                    assets[str(asset['id']).lower()] = asset

        return assets.values()
