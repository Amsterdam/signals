from .Evaluator import Evaluator

class EqualityEvaluator(Evaluator):
    def __init__(self, **kwargs):
        # '==' | '!=' | '<' | '<=' | '>' | '>='
        self._CMD_MAP = {
            '==' : self._eq_handler,
            '!=' : self._neq_handler,
            '<' : self._lt_handler,
            '<=' : self._lte_handler,
            '>' : self._gt_handler,
            '>=' : self._gte_handler,
        }

        self.lhs = kwargs.pop('lhs')
        self.op = kwargs.pop('op')
        self.rhs = kwargs.pop('rhs')
    
    def evaluate(self, ctx):
        if self.op in self._CMD_MAP:
            return self._CMD_MAP[self.op](ctx)
        else:
            raise Exception("Equality operator: '{}' is not supported".format(self.op))
    
    def _eq_handler(self, ctx):
        return self.lhs.evaluate(ctx) == self.rhs.evaluate(ctx)

    def _neq_handler(self, ctx):
        return self.lhs.evaluate(ctx) != self.rhs.evaluate(ctx)

    def _lt_handler(self, ctx):
        return self.lhs.evaluate(ctx) < self.rhs.evaluate(ctx)

    def _lte_handler(self, ctx):
        return self.lhs.evaluate(ctx) <= self.rhs.evaluate(ctx)

    def _gt_handler(self, ctx):
        return self.lhs.evaluate(ctx) > self.rhs.evaluate(ctx)

    def _gte_handler(self, ctx):
        return self.lhs.evaluate(ctx) >= self.rhs.evaluate(ctx)
