# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from signals.apps.dsl.evaluators.evaluator import Evaluator


class LogicalEvaluator(Evaluator):
    def __init__(self, **kwargs):
        self._CMD_MAP = {
            'and': self._and_handler,
            'or': self._or_handler,
        }

        self.lhs = kwargs.pop('lhs')
        self.rhs = kwargs.get('rhs', None)

    def evaluate(self, ctx):
        if not self.rhs:
            return self.lhs.evaluate(ctx)
        else:
            if self.op in self._CMD_MAP:
                return self._CMD_MAP[self.op](ctx)
            else:
                raise Exception("logical operator: '{}' is not supported".format(self.op))

    def _and_handler(self, ctx):
        ret = self.lhs.evaluate(ctx)
        # short circuit
        if not ret:
            return False
        for op in self.rhs:
            if not op.evaluate(ctx):
                return False
        return True

    def _or_handler(self, ctx):
        ret = self.lhs.evaluate(ctx)
        # short circuit
        if ret:
            return True
        for op in self.rhs:
            if op.evaluate(ctx):
                return True
        return False
