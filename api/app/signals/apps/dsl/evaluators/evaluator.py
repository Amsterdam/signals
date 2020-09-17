from abc import ABC, abstractmethod


class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, ctx):
        pass

    def resolve(self, ctx, ident):
        if ident in ctx:
            return ctx[ident]
        else:
            raise Exception("Could not resolve ident: '{}'".format(ident))
