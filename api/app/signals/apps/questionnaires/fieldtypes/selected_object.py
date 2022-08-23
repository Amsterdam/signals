# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from signals.apps.questionnaires.fieldtypes.base import FieldType


class SelectedObject(FieldType):
    verbose_name = 'Selected object'
    submission_schema = {
        'type': 'object',
        'properties': {
            'id': {
                'anyOf': [
                    {
                        'type': 'integer',
                        'minimum': 0
                    },
                    {
                        'type': 'string'
                    }
                ]
            },
            'label': {
              'type': 'string'
            },
            'answer': {
                'anyOf': [
                    {
                        'type': 'object',
                        'required': [
                            'type',
                        ],
                        'properties': {
                            'type': {
                                'type': 'string',
                                'pattern': '^not-on-map$',
                            },
                        },
                    },
                    {
                        'type': 'object',
                        'required': [
                            'id',
                            'type',
                            'label',
                        ],
                        'properties': {
                            'id': {
                                'type': 'integer',
                                'minimum': 0,
                            },
                            'type': {
                                'type': 'string',
                                'pattern': '^not-on-map$',
                            },
                            'label': {
                                'type': 'string',
                            }
                        },
                    },
                    {
                        'type': 'object',
                        'required': [
                            'id',
                            'type',
                            'description',
                            'label',
                        ],
                        'properties': {
                            'id': {
                                'anyOf': [
                                    {
                                        'type': 'integer',
                                        'minimum': 0
                                    },
                                    {
                                        'type': 'string'
                                    }
                                ]
                            },
                            'type': {
                                'type': 'string',
                            },
                            'description': {
                                'type': 'string',
                            },
                            'isReported': {
                                'type': 'boolean',
                            },
                            'label': {
                                'type': 'string',
                            },
                            'location': {
                                'type': 'object',
                                'properties': {
                                    'address': {
                                        'type': 'object',
                                        'properties': {
                                            'postcode': {
                                                'type': 'string',
                                                'pattern': '^[1-9][0-9]{3} ?[A-Za-z]{2}$',
                                            },
                                            'huisnummer': {
                                                'anyOf': [
                                                    {
                                                        'type': 'integer',
                                                        'minimum': 0
                                                    },
                                                    {
                                                        'type': 'string'
                                                    }
                                                ]
                                            },
                                            'woonplaats': {
                                                'type': 'string',
                                            },
                                            'openbare_ruimte': {
                                                'type': 'string',
                                            }
                                        },
                                    },
                                    'coordinates': {
                                        'type': 'object',
                                        'required': [
                                            'lat',
                                            'lng',
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
                            },
                            'status': {
                                'type': 'string'
                            },
                        },
                    },
                ],
            },
            "category_url": {
                "format": "regex",
                "pattern": "^((https?://(www.|)([\\w\\d.:]*)|)(/[\\w\\d\\-/]+))$"
            },
        },
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
