from signals.apps.signals.factories import SignalDepartmentsFactory


class DirectingDepartmentsFactory(SignalDepartmentsFactory):
    relation_type = 'directing'
