import time
from evaluators import MetaModel
from django.contrib.gis import geos

TEST_GRAMMAR='''
RootExpression: expression = OrExpression;
OrExpression: lhs=AndExpression ('or' rhs=AndExpression)?;
AndExpression: lhs=BinaryExpression ('and' rhs=BinaryExpression)?;
BinaryExpression: InExpression | EqualityExpression | ('(' OrExpression ')');

EqualityExpression: lhs=TermExpression op=EqualityOperand rhs=TermExpression;
EqualityOperand: '==' | '!=' | '<=' | '<' | '>=' | '>';
InExpression: lhs=TermStringExpression 'in' rhs=TermStringExpression ('.' rhs_prop=TermStringExpression)*;
TermExpression: TermTimeExpression | TermStringExpression | TermNumericExpression;
TermStringExpression: str_val=STRING | id_val=ID;
TermNumericExpression: numeric_val=NUMBER;
TermTimeExpression: time_val=/\d{1,2}\:\d{2}(\:\d{2})?/;

Comment: /\/\/.*$/;
'''

TEST_EXPR ='''
//testint < 0
(time <= 20:00:00 and time >= 08:00:00) 
//and location in area."stadsdeel"."oost"
//or (maincat == "eikenprocessierups" and (subcat == bomen or subcat == afval))
'''
 

def main():
    mm = MetaModel(TEST_GRAMMAR)
    model = mm.model_from_str(TEST_EXPR)

    # we can fill identifiers with the values, these can be resolved via the evaluators resolve() method
    poly = geos.Polygon( ((0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0), (0.0, 0.0)) )
    context = {
        'testint' : 1,
        'location' : geos.Point(5, 23),
        'maincat' : 'dieren',
        'subcat' : 'subcat',
        'time' : time.strptime("16:00:00", "%H:%M:%S"),
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