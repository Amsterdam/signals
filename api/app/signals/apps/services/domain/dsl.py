# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
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
        tmp = {
            'sub': signal.category_assignment.category.name,
            'main': signal.category_assignment.category.parent.name,
            'location': signal.location.geometrie,
            'stadsdeel': signal.location.stadsdeel,
            'time': time.strptime(t, "%H:%M:%S"),
            'day': signal.incident_date_start.strftime("%A"),
            'areas': self.areas
        }

        # add additonal question answers id to context
        if signal.extra_properties:
            for prop in signal.extra_properties:
                if 'id' in prop and 'answer' in prop and prop['id'] not in tmp:
                    answer = prop['answer']
                    # UI elements can be a list of dicts with 'label' or 'value' keys
                    # or a single dict with 'label' or 'value' keys
                    if type(answer) is list:
                        tmp[prop['id']] = set(
                            [x.get('label', x.get('value', None)) for x in answer if type(x) is dict]
                        )
                    elif type(answer) is dict:
                        tmp[prop['id']] = answer.get('label', answer.get('value', None))
                    else:
                        tmp[prop['id']] = prop['answer']

        return tmp


class SignalDslService(DslService):
    context_func = SignalContext()
    signal_manager = SignalManager()

    def process_routing_rules(self, signal):
        ctx = self.context_func(signal)
        rules = RoutingExpression.objects.select_related('_expression', '_department')
        for rule in rules.filter(is_active=True, _expression___type__name='routing').order_by('order'):
            evaluator = None
            try:
                evaluator = self._compile(rule._expression.code)
            except Exception:
                # compilation failed, invalidate rule
                rule.is_active = False
                rule.save()

            if evaluator and rule.is_active:
                eval_result = False
                try:
                    eval_result = evaluator.evaluate(ctx)
                except Exception:
                    # ignore runtime errors
                    pass
                if eval_result:
                    # assign relation to department
                    data = {
                        'routing_assignment': {
                            'departments': [
                                {
                                    'id': rule._department.id
                                }
                            ]
                        },
                        'user_assignment': {
                            'user': {
                                'email': None if not rule._user else rule._user.email
                            }
                        }
                    }
                    self.signal_manager.update_multiple(data, signal)
                    return True
        return False
