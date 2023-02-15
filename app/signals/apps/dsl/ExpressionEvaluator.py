# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from signals.apps.dsl.evaluators.meta_model import MetaModel

GRAMMAR = '''
RootExpression: expression = OrExpression;
OrExpression: lhs=AndExpression ('or' rhs=AndExpression)*;
AndExpression: lhs=BinaryExpression ('and' rhs=BinaryExpression)*;
BinaryExpression: InExpression | EqualityExpression | ('(' OrExpression ')') ;
EqualityExpression: lhs=TermExpression op=EqualityOperand rhs=TermExpression;
EqualityOperand: '==' | '!=' | '<=' | '<' | '>=' | '>';
InExpression: lhs=TermStringExpression 'in' rhs=TermStringExpression ('.' rhs_prop=TermStringExpression)*;
TermExpression: TermTimeExpression | TermStringExpression | TermNumericExpression;
TermStringExpression: str_val=STRING | id_val=ID;
TermNumericExpression: numeric_val=NUMBER;
TermTimeExpression: time_val=/\d{1,2}\:\d{2}(\:\d{2})?/;
Comment: /\/\/.*$/;
''' # noqa


class ExpressionEvaluator:
    mm = MetaModel(GRAMMAR)

    def compile(self, code):
        return self.mm.model_from_str(code)
