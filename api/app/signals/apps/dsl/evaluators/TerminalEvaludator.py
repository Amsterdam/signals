from .Evaluator import Evaluator

class TerminalEvaluator(Evaluator):
    id_val = None
    str_val = None
    int_val = None
    float_val = None
    def __init__(self, **kwargs):
        self.id_val = kwargs.get('id_val', None)
        self.str_val = kwargs.get('str_val', None)
        self.int_val = kwargs.get('int_val', None)
        self.float_val = kwargs.get('float_val', None)

    def evaluate(self, ctx):
        if self.id_val:
            return self.resolve(ctx, self.id_val)
        if self.str_val:
            return self.str_val
        if self.int_val:
            return self.int_val
        if self.float_val:
            return self.float_val

        raise Exception("No value for term evaluator")