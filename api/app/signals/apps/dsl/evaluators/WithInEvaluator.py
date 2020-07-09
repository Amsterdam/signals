import time
from .Evaluator import Evaluator

class WithInEvaluator(Evaluator):

    def __init__(self, **kwargs):
        self.lhs = kwargs.pop('lhs')
        self.rhs = kwargs.pop('rhs')
    
    def evaluate(self, ctx):
        # resolve symbols
        lhs = self.resolve(ctx, self.lhs)
        rhs = self.resolve(ctx, self.rhs)
        return lhs in rhs