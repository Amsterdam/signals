from textx import metamodel_from_str

from signals.apps.dsl.evaluators.equality_evaluator import EqualityEvaluator
from signals.apps.dsl.evaluators.in_evaluator import InEvaluator
from signals.apps.dsl.evaluators.logical_evaluator import LogicalEvaluator
from signals.apps.dsl.evaluators.root_evaluator import RootEvaluator
from signals.apps.dsl.evaluators.terminal_evaluator import TerminalEvaluator

# user classes have to live in the same module-space where the metamodel_from_str is invoked.
# the names should exactly match the rule-name, we will just subclass them here with the correct name


class RootExpression(RootEvaluator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class EqualityExpression(EqualityEvaluator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class OrExpression(LogicalEvaluator):
    op = 'or'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class AndExpression(LogicalEvaluator):
    op = 'and'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class InExpression(InEvaluator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TermStringExpression(TerminalEvaluator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TermNumericExpression(TerminalEvaluator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TermTimeExpression(TerminalEvaluator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MetaModel(object):
    def __init__(self, grammar):
        self.mm = metamodel_from_str(
            lang_desc=grammar,
            classes=[
                RootExpression, EqualityExpression, OrExpression, AndExpression, InExpression,
                TermStringExpression, TermNumericExpression, TermTimeExpression
            ],
            debug=False
        )

    def model_from_str(self, model):
        return self.mm.model_from_str(model)
