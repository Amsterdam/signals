import time

from signals.apps.dsl.ExpressionEvaluator import ExpressionEvaluator
from signals.apps.signals.managers import SignalManager
from signals.apps.signals.models import Area, AreaType, RoutingExpression, Signal


class DslService:
    compiler = ExpressionEvaluator()
    _code_cache = {}

    def _compile(self, code):
        if code not in self._code_cache:
            self._code_cache[code] = self.compiler.compile(code)
        return self._code_cache[code]

    def evaluate(self, context, code):
        evaluator = self._compile(code)
        return evaluator.evaluate(context)

    def validate(self, context, code):
        try:
            self.evaluate(context, code)
            return None
        except Exception as e:
            return str(e)


# maps signal object to context dictionary
class SignalContext:
    _areas = None

    def _init_areas(self):
        tmp = {}
        for area_type in AreaType.objects.all():
            tmp[area_type.name] = {
                area.code: area.geometry for area in Area.objects.filter(_type=area_type).all()
            }
        return tmp

    @property
    def areas(self):
        if not self._areas:
            self._areas = self._init_areas()
        return self._areas

    def __call__(self, signal: Signal):

        t = signal.incident_date_start.strftime("%H:%M:%S")
        return {
            'sub': signal.category_assignment.category.name,
            'main': signal.category_assignment.category.parent.name,
            'location': signal.location.geometrie,
            'stadsdeel': signal.location.stadsdeel,
            'time': time.strptime(t, "%H:%M:%S"),
            'areas': self.areas
        }


class SignalDslService(DslService):
    context_func = SignalContext()
    signal_manager = SignalManager()

    def process_routing_rules(self, signal):
        ctx = self.context_func(signal)
        rules = RoutingExpression.objects.select_related('_expression', '_department')
        for rule in rules.filter(is_active=True, _expression___type__name='routing').order_by('order'):
            if self.evaluate(signal, rule._expression.code, ctx):
                # assign relation to department
                data = {
                    'relation_type': 'routing',
                    'departments': [
                        {
                            'id': rule._department.id
                        }
                    ]
                }
                self.signal_manager.update_routing_departments(data, signal)
                return True
        return False

    def evaluate(self, signal, code, ctx=None):
        if not ctx:
            ctx = self.context_func(signal)
        return super().evaluate(ctx, code)
