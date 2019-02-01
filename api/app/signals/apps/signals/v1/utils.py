from collections import namedtuple

SplitSignalData = namedtuple('SplitSignalData', [
    'validated_data',
    'location_data',
    'initial_status',
    'category_assignment_data',
    'reporter_data',
    'priority_data',
    'created_by', ])
