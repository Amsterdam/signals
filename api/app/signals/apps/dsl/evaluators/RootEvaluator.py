from signals.apps.dsl.evaluators.Evaluator import Evaluator


class RootEvaluator(Evaluator):
    def __init__(self, **kwargs):
        self.expression = kwargs.pop('expression')

    def evaluate(self, ctx):
        return self.expression.evaluate(ctx)
