# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import time

from signals.apps.dsl.evaluators.evaluator import Evaluator


class TerminalEvaluator(Evaluator):
    bool_val = None
    id_val = None
    prop_val = None
    str_val = None
    numeric_val = None
    time_val = None

    def __init__(self, **kwargs):
        self.bool_val = kwargs.get('bool_val', None)
        self.id_val = kwargs.get('id_val', None)
        self.prop_val = kwargs.get('prop_val', [])
        self.str_val = kwargs.get('str_val', None)
        self.numeric_val = kwargs.get('numeric_val', None)
        self.time_val = kwargs.get('time_val', None)

    def _convert(self, s, flist=['%H:%M:%S', '%H:%M']):
        for f in flist:
            try:
                return time.strptime(s, f)
            except ValueError:
                pass

    def evaluate(self, ctx):
        if self.bool_val is not None:
            return self.bool_val.lower() == 'true'
        if self.id_val:
            value = self.resolve(ctx, self.id_val)
            for prop in self.prop_val:
                value = value[prop]
            return value
        if self.str_val:
            return self.str_val
        if self.time_val:
            return self._convert(self.time_val)
        if self.numeric_val is not None:
            return self.numeric_val

        raise Exception("No value for term evaluator")
