from .Evaluator import Evaluator

class LogicalEvaluator(Evaluator):
    def __init__(self, **kwargs):
        self._CMD_MAP = {
            'and' : self._and_handler,
            'or' : self._or_handler,
        }

        self.lhs = kwargs.pop('lhs')
        #self.op = kwargs.get('op', None)
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
        lval = self.lhs.evaluate(ctx)
        # short circuit
        if not lval:
            return False
        return self.rhs.evaluate(ctx)

    def _or_handler(self, ctx):
        lval = self.lhs.evaluate(ctx)
        # short circuit
        if lval:
            return True
        return self.rhs.evaluate(ctx)
