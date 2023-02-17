# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from signals.apps.dsl.evaluators.evaluator import Evaluator


class RootEvaluator(Evaluator):
    def __init__(self, **kwargs):
        self.expression = kwargs.pop('expression')

    def evaluate(self, ctx):
        return self.expression.evaluate(ctx)
