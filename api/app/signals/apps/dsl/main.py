import time
from evaluators import MetaModel

TEST_GRAMMAR='''
RootExpression: expressions *= LogicalExpression;
LogicalExpression: lhs=Expression (op=Logical rhs=Expression)*;
Logical: 'and' | 'or';
Expression: WithInExpression | EqualityExpression | TimeExpression | ('(' LogicalExpression ')');
WithInExpression: lhs=ID 'within' rhs=ID;
EqualityExpression: lhs=ID op=EqualityOperand rhs=ID;
EqualityOperand: '==' | '!=' | '<' | '<=' | '>' | '>=';
TimeExpression: lhs=ID 'in' start=STRING ',' end=STRING;
'''

TEST_GRAMMAR2='''
RootExpression: expression = OrExpression;
OrExpression: lhs=AndExpression ('or' rhs=AndExpression)?;
AndExpression: lhs=BinaryExpression ('and' rhs=BinaryExpression)?;
BinaryExpression: InExpression | EqualityExpression | ('(' OrExpression ')');

EqualityExpression: lhs=ID op=EqualityOperand rhs=ID;
EqualityOperand: '==' | '!=' | '<' | '<=' | '>' | '>=';
InExpression: lhs=ID 'in' (rhs=STRING | rhs=ID ('.' rhs_prop=ID)?);

Comment: /\/\/.*$/;
'''

TEST_EXPR ='''
location in stadsdeel.oost
and time in "20:00-00:00"
or (category == eikenprocessierups and (subcat == bomen or subcat == afval))
'''
 

def main():
    mm = MetaModel(TEST_GRAMMAR2)
    model = mm.model_from_str(TEST_EXPR)

    # we can fill identifiers with the values, these can be resolved via the evaluators resolve() method
    context = {
        'location' : 'geo1',
        'maincat' : 'dieren',
        'subcat' : 'subcat',
        'time' : time.time(),
        'stadsdeel' : set(['geo1', 'geo2'])
    }

    result = model.evaluate(context)
    print(result)

if __name__ == '__main__':
    main()