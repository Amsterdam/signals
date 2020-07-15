from django.contrib.gis import geos

from signals.apps.dsl.evaluators.Evaluator import Evaluator


class InEvaluator(Evaluator):
    _TIME_FORMAT = '%H:%M:%S'

    def __init__(self, **kwargs):
        self._CMD_MAP = {
            'str': self._list_handler,
            'point': self._geo_handler,
        }

        self.lhs = kwargs.pop('lhs')
        self.rhs = kwargs.pop('rhs')
        self.rhs_prop = kwargs.get('rhs_prop', None)

    def _get_type(self, obj):
        if isinstance(obj, str):
            return 'str'
        elif isinstance(obj, geos.Point):
            return 'point'
        else:
            return 'unknown'

    def _rais_type_error(self, exp, act):
        raise Exception("Error: expected: '{exp}', actual: '{act}'".format(exp=exp, act=act))

    def evaluate(self, ctx):
        lhs_val = self.lhs.evaluate(ctx)
        lhs_type = self._get_type(lhs_val)
        if lhs_type in self._CMD_MAP:
            return self._CMD_MAP[lhs_type](ctx, lhs_val)
        else:
            raise Exception("No 'in' handler for type: '{}'".format(lhs_type))

    def _list_handler(self, ctx, lhs_val):
        rhs_val = self.rhs.evaluate(ctx)
        if type(rhs_val) is not set:
            self._rais_type_error(exp=type(set), act=type(rhs_val))
        return lhs_val in rhs_val

    def _geo_handler(self, ctx, lhs_val):
        rhs_val = self.rhs.evaluate(ctx)
        if self.rhs_prop and len(self.rhs_prop) > 0:
            try:
                for prop in self.rhs_prop:
                    rhs_val = rhs_val[prop.evaluate(ctx)]
            except KeyError:
                raise Exception("Could not resolve {prop}".format(prop=".".join(self.rhs_prop)))
        if type(rhs_val) is not geos.MultiPolygon:
            self._rais_type_error(exp=type(geos.MultiPolygon), act=type(rhs_val))
        return rhs_val.within(lhs_val)
