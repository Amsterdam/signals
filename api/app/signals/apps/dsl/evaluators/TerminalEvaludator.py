import time

from signals.apps.dsl.evaluators.Evaluator import Evaluator


class TerminalEvaluator(Evaluator):
    id_val = None
    str_val = None
    numeric_val = None
    time_val = None

    def __init__(self, **kwargs):
        self.id_val = kwargs.get('id_val', None)
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
        if self.id_val:
            return self.resolve(ctx, self.id_val)
        if self.str_val:
            return self.str_val
        if self.time_val:
            return self._convert(self.time_val)
        if self.numeric_val is not None:
            return self.numeric_val

        raise Exception("No value for term evaluator")
