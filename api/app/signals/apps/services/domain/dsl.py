import time

from signals.apps.dsl.ExpressionEvaluator import ExpressionEvaluator
from signals.apps.signals.models import Area, AreaType, Signal


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
    _areas = {}

    def __init__(self):
        for area_type in AreaType.objects.all():
            self._areas[area_type.name] = {
                area.code: area.geometry for area in Area.objects.filter(_type=area_type).all()
            }

    def __call__(self, signal: Signal):

        t = signal.incident_date_start.strftime("%H:%M:%S")
        return {
            'sub': signal.category_assignment.category.name,
            'main': signal.category_assignment.category.parent.name,
            'location': signal.location.geometrie,
            'stadsdeel': signal.location.stadsdeel,
            'time': time.strptime(t, "%H:%M:%S"),
            'areas': self._areas
        }


class SignalDslService(DslService):
    context_func = SignalContext()

    def evaluate(self, signal, code):
        ctx = self.context_func(signal)
        return super().evaluate(ctx, code)
