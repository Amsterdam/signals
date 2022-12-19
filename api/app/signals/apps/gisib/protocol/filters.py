# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import json
from dataclasses import dataclass


@dataclass
class Filters:
    filters: list

    def as_list(self):
        return [_filter.as_dict() for _filter in self.filters]

    def json(self):
        return json.dumps(self.as_list())


@dataclass
class Filter:
    criterias: list
    operator: str = 'AND'

    def as_dict(self):
        return {
            'Criterias': [criteria.as_dict() for criteria in self.criterias],
            'Operator': self.operator
        }

    def json(self):
        return json.dumps(self.as_dict())


@dataclass
class Criteria:
    property: str
    value: str
    operator: str

    def as_dict(self):
        return {
            'Property': self.property,
            'Value': self.value,
            'Operator': self.operator
        }

    def json(self):
        return json.dumps(self.as_dict())
