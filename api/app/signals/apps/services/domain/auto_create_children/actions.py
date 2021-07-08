# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import requests
from django.contrib.gis.geos import Point

from signals.apps.services.domain.auto_create_children.mixins import ExtraPropertiesMixin
from signals.apps.services.domain.auto_create_children.rules import (
    ContainerRule,
    EikenprocessierupsRule
)
from signals.apps.signals.models import Category, Signal
from signals.apps.signals.workflow import GEMELD


class CreateChildrenContainerAction(ExtraPropertiesMixin):
    rule = ContainerRule()

    type_2_category_slug = {
        'rest': 'container-is-vol',
        'papier': 'container-voor-papier-is-vol',
        'plastic': 'container-voor-plastic-afval-is-vol',
        'glas': 'container-glas-vol',
        'default': 'container-is-vol',
    }

    def _translate_type_2_category(self, container_type):
        lowered_container_type = container_type.lower()
        slug = self.type_2_category_slug['default']
        if lowered_container_type in self.type_2_category_slug:
            slug = self.type_2_category_slug[lowered_container_type]
        return Category.objects.get(slug=slug)

    def _get_container_location(self, id_number, default=None):
        """
        Get the location of the given container. If the container cannot be found the default will be returned

        API: https://api.data.amsterdam.nl/v1/huishoudelijkafval/container
        Schema: https://schemas.data.amsterdam.nl/datasets/huishoudelijkafval/huishoudelijkafval

        An example of a response can be found in tests/apps/services/domain/json/huidhoudelijkafval.json
        """
        endpoint = f'https://api.data.amsterdam.nl/v1/huishoudelijkafval/container/?idNummer={id_number}'
        response = requests.get(endpoint)
        response_json = response.json()
        if response.status_code == 200 and len(response_json['_embedded']['container']) == 1:
            coordinates = response_json['_embedded']['container'][0]['geometrie']['coordinates']
            geometry = Point(coordinates[0], coordinates[1], srid=28992)
            geometry.transform(ct=4326)
            return geometry
        return default

    def run(self, signal):
        for container_data in self.get_extra_properties(signal, 'extra_container'):
            category = self._translate_type_2_category(container_data['type'])
            geometry = self._get_container_location(container_data['id'], signal.location.geometrie)

            signal_data = {
                'text': signal.text,
                'text_extra': signal.text_extra,
                'incident_date_start': signal.incident_date_start,
                'parent': signal,
                'extra_properties': [
                    {
                        'id': 'extra_container',
                        'label': 'Container(s)',
                        'answer': [
                            container_data
                        ],
                        'category_url': category.get_absolute_url()
                    }
                ]
            }
            location_data = {
                'geometrie': geometry,
            }
            status_data = {
                'state': GEMELD,
            }
            category_data = {
                'category': category,
            }

            # Create the child signal using the actions manager
            child_signal = Signal.actions.create_initial(signal_data, location_data, status_data, category_data, {})

            # Copy attachments to the child signal
            attachments_qs = signal.attachments.filter(is_image=True)
            if attachments_qs.count():
                Signal.actions.copy_attachments(data=attachments_qs.all(), signal=child_signal)

    def __str__(self):
        return f'{self.__class__.__name__}'

    def __call__(self, signal):
        if not self.rule(signal):
            return False

        self.run(signal)
        return True


class CreateChildrenEikenprocessierupsAction(ExtraPropertiesMixin):
    rule = EikenprocessierupsRule()

    def run(self, signal):
        for eikenprocessierups_data in self.get_extra_properties(signal, 'extra_eikenprocessierups'):
            signal_data = {
                'text': signal.text,
                'text_extra': signal.text_extra,
                'incident_date_start': signal.incident_date_start,
                'parent': signal,
                'extra_properties': [
                    {
                        'id': 'extra_eikenprocessierups',
                        'label': 'Boom',
                        'answer': [
                            eikenprocessierups_data
                        ],
                        'category_url': signal.category_assignment.category.get_absolute_url()
                    }
                ]
            }
            location_data = {
                'geometrie': signal.location.geometrie,
            }
            status_data = {
                'state': GEMELD,
            }
            category_data = {
                'category': signal.category_assignment.category,
            }

            # Create the child signal using the actions manager
            child_signal = Signal.actions.create_initial(signal_data, location_data, status_data, category_data, {})

            # Copy attachments to the child signal
            attachments_qs = signal.attachments.filter(is_image=True)
            if attachments_qs.count():
                Signal.actions.copy_attachments(data=attachments_qs.all(), signal=child_signal)

    def __str__(self):
        return f'{self.__class__.__name__}'

    def __call__(self, signal):
        if not self.rule(signal):
            return False

        self.run(signal)
        return True
