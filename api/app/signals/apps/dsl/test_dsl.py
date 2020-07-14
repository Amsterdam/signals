import time

from django.contrib.gis import geos

from ExpressionEvaluator import ExpressionEvaluator

TEST_EXPR = '''
maincat == "dieren"
//lijstval in lijstje
//testint > 0
//and (time <= 20:00:00 and time >= 08:00:00)
//and location in area."stadsdeel"."oost"
//or (maincat == "dieren" and (subcat == bomen or subcat == "eikenprocessierups"))
'''


def main():
    compiler = ExpressionEvaluator()
    evaluator = compiler.compile(TEST_EXPR)

    # we can fill identifiers with the values, these can be resolved via the evaluators resolve() method
    poly = geos.Polygon(
        ((0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0), (0.0, 0.0))
    )

    context = {
        'testint': 1,
        'location': geos.Point(5, 23),
        'maincat': 'dieren',
        'subcat': 'subcat',
        'time': time.strptime("16:00:00", "%H:%M:%S"),
        'area': {
            'stadsdeel': {
                'oost': geos.MultiPolygon(poly)
            }
        },
        'lijstval': 'geo1',
        'lijstje': set(['geo1', 'geo2'])
    }

    result = evaluator.evaluate(context)
    print(result)


if __name__ == '__main__':
    main()
