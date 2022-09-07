# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from signals.apps.questionnaires.fieldtypes.base import FieldType


class SelectedObject(FieldType):
    verbose_name = 'Selected object'

    # Example of a JSON object that is accepted by this schema:
    #
    # {
    #   "id": 123456789,
    #   "type": "papier-container",
    #   "on-map": true,
    #   "coordinates": {
    #     "lat": 4.75029,
    #     "lng": 51.198302
    #   }
    # }
    submission_schema = {
        'type': 'object',
        'properties': {
            'id': {
                'anyOf': [
                    {
                        'type': 'integer',
                        'min': 0
                    },
                    {
                        'type': 'string',
                        'minLength': 1
                        },
                    {
                        'type': 'null'
                    }
                ]
            },
            'type': {
                'type': 'string'
            },
            'on-map': {
                'type': 'boolean'
            },
            'coordinates': {
                'type': 'object',
                'required': [
                    'lat',
                    'lng'
                ],
                'properties': {
                    'lat': {
                        'type': 'number',
                        'minimum': -90,
                        'maximum': 90
                    },
                    'lng': {
                        'type': 'number',
                        'minimum': -180,
                        'maximum': 180
                    }
                }
            }
        },
        'required': [
            'id',
            'type',
            'on-map',
            'coordinates'
        ]
    }

    # The question_extra_properties_schema defines which extra properties are allowed for a specific question type.
    #
    # To select an object from a list of objects, the following extra properties are allowed:
    # - source_url: The url to the source of the list of objects
    extra_properties_schema = {
        'type': 'object',
        'properties': {
            'source_url': {
                'type': 'string',
                'format': 'uri',
            },
        },
        'required': [
            'source_url',
        ],
        'additionalProperties': False
    }
