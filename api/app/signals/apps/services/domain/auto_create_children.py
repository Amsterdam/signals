# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import logging

import requests
from django.conf import settings
from django.contrib.gis.geos import Point

from signals.apps.signals.models import Category, Signal
from signals.apps.signals.workflow import GEMELD

log = logging.getLogger(__name__)


class AutoCreateChildrenService:
    """
    !!! This will be refactored when the "uitvraag" will be moved to the API !!!

    Automatically create child signals if:
        - The feature flag "AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_CONTAINER" is enabled
        - A signal is not a parent or a child signal
        - A signal has the status "GEMELD" ("m")
        - A signal belongs to the sub category "container-is-vol", "container-voor-papier-is-vol", "container-voor-plastic-afval-is-vol" or "container-glas-vol"
        - A signal must contain at least 2 or more containers but not more than the value of the setting SIGNAL_MAX_NUMBER_OF_CHILDREN
        
        For now this is only used to create child signals when multiple containers are selected.
    """  # noqa

    _type_2_category_slug = {
        'rest': 'container-is-vol',
        'papier': 'container-voor-papier-is-vol',
        'plastic': 'container-voor-plastic-afval-is-vol',
        'glas': 'container-glas-vol',
        'default': 'container-is-vol',
    }

    @staticmethod
    def _get_container_location(id_number, default=None):
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

    @staticmethod
    def _translate_type_2_category(container_type):
        slug = AutoCreateChildrenService._type_2_category_slug['default']
        if container_type.lower() in AutoCreateChildrenService._type_2_category_slug:
            slug = AutoCreateChildrenService._type_2_category_slug[container_type.lower()]
        return Category.objects.get(slug=slug)

    @staticmethod
    def _container_data(signal):
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
        if not signal.extra_properties:
            return []

        containers = {}
        for extra_property in signal.extra_properties:
            if extra_property.get('id', '').lower() == 'extra_container':
                for container in extra_property['answer']:
                    containers[str(container['id']).lower()] = container

        return containers.values()

    @staticmethod
    def _is_applicable(signal):
        """
        - A signal is not a parent or a child signal
        - A signal has the status "GEMELD" ("m")
        - A signal belongs to the sub category "container-is-vol", "container-voor-papier-is-vol", "container-voor-plastic-afval-is-vol" or "container-glas-vol"
        - A signal must contain at least 2 or more containers but not more than the value of the setting SIGNAL_MAX_NUMBER_OF_CHILDREN
        
        For now this is only used to create child signals when multiple containers are selected.
        """  # noqa
        if signal.is_parent or signal.is_child or signal.status.state != GEMELD:
            return False

        category_slug = signal.category_assignment.category.slug
        if category_slug not in set(AutoCreateChildrenService._type_2_category_slug.values()):
            return False

        selected_containers = len(AutoCreateChildrenService._container_data(signal))
        if selected_containers < 2:
            return False

        if selected_containers > settings.SIGNAL_MAX_NUMBER_OF_CHILDREN:
            return False

        return True

    @staticmethod
    def _create_child(signal, container_data):
        category = AutoCreateChildrenService._translate_type_2_category(container_data['type'])
        geometry = AutoCreateChildrenService._get_container_location(container_data['id'], signal.location.geometrie)

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
        Signal.actions.create_initial(signal_data, location_data, status_data, category_data, {})

    @staticmethod
    def run(signal_id):
        if not settings.FEATURE_FLAGS.get('AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_CONTAINER', False):
            return

        signal = Signal.objects.get(pk=signal_id)

        if not AutoCreateChildrenService._is_applicable(signal=signal):
            return

        containers_data = AutoCreateChildrenService._container_data(signal)
        for container_data in containers_data:
            AutoCreateChildrenService._create_child(signal, container_data)
