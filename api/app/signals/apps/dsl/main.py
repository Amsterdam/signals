import time
from evaluators import MetaModel
from django.contrib.gis import geos

TEST_GRAMMAR='''
RootExpression: expression = OrExpression;
OrExpression: lhs=AndExpression ('or' rhs=AndExpression)?;
AndExpression: lhs=BinaryExpression ('and' rhs=BinaryExpression)?;
BinaryExpression: NumericExpression | InExpression | EqualityExpression | ('(' OrExpression ')');

EqualityExpression: lhs=TermExpression op=EqualityOperand rhs=TermExpression;
EqualityOperand: '==' | '!=' | '<' | '<=' | '>' | '>=';
InExpression: lhs=TermExpression 'in' (rhs=TermExpression ('.' rhs_prop=TermExpression)*);
TermExpression: STRING | ID;
NumericExpression: INT | FLOAT;

Comment: /\/\/.*$/;
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
location in area."stadsdeel"."oost"
and time in "20:00-00:00"
or (category == eikenprocessierups and (subcat == bomen or subcat == afval))
'''
 

def main():
    mm = MetaModel(TEST_GRAMMAR)
    model = mm.model_from_str(TEST_EXPR)

    # we can fill identifiers with the values, these can be resolved via the evaluators resolve() method
    poly = geos.Polygon( ((0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0), (0.0, 0.0)) )
    context = {
        'location' : geos.Point(5, 23),
        'maincat' : 'dieren',
        'subcat' : 'subcat',
        'time' : time.time(),
        'area' : {
            'stadsdeel' : {
                'oost' : geos.MultiPolygon(poly)
            }
        },
        'lijstje' : set(['geo1', 'geo2'])
    }

    result = model.evaluate(context)
    print(result)

if __name__ == '__main__':
    main()