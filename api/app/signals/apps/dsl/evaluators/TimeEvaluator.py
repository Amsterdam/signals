import time
from .Evaluator import Evaluator

class TimeEvaluator(Evaluator):
    _TIME_FORMAT = '%H:%M:%S'

    def __init__(self, **kwargs):
        self.lhs = kwargs.pop('lhs')
        self.start = kwargs.pop('start')
        self.end = kwargs.pop('end')
    
    def evaluate(self, ctx):
        start = time.strptime(self.start, self._TIME_FORMAT)
        end = time.strptime(self.end, self._TIME_FORMAT)
        current = self.resolve(ctx, self.lhs)
        current = time.strptime(current, self._TIME_FORMAT)
        return current >= start and current <= end