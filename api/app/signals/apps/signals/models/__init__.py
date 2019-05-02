from signals.apps.signals.models.attachment import Attachment
from signals.apps.signals.models.buurt import Buurt
from signals.apps.signals.models.category import Category
from signals.apps.signals.models.category_assignment import CategoryAssignment
from signals.apps.signals.models.department import Department
from signals.apps.signals.models.history import History
from signals.apps.signals.models.location import (
    STADSDEEL_CENTRUM,
    STADSDEEL_NIEUWWEST,
    STADSDEEL_NOORD,
    STADSDEEL_OOST,
    STADSDEEL_WEST,
    STADSDEEL_WESTPOORT,
    STADSDEEL_ZUID,
    STADSDEEL_ZUIDOOST,
    STADSDELEN,
    Location,
    get_address_text
)
from signals.apps.signals.models.mixins import CreatedUpdatedModel
from signals.apps.signals.models.note import Note
from signals.apps.signals.models.priority import Priority
from signals.apps.signals.models.reporter import Reporter
from signals.apps.signals.models.signal import Signal
from signals.apps.signals.models.status import Status
from signals.apps.signals.models.text import Text

# Satisfy Flake8 (otherwise complaints about unused imports):
__all__ = [
    'Attachment',
    'Buurt',
    'Category',
    'CategoryAssignment',
    'Department',
    'History',
    'STADSDEEL_CENTRUM',
    'STADSDEEL_NIEUWWEST',
    'STADSDEEL_NOORD',
    'STADSDEEL_OOST',
    'STADSDEEL_WEST',
    'STADSDEEL_WESTPOORT',
    'STADSDEEL_ZUID',
    'STADSDEEL_ZUIDOOST',
    'STADSDELEN',
    'Location',
    'get_address_text',
    'CreatedUpdatedModel',
    'Note',
    'Priority',
    'Reporter',
    'Signal',
    'Status',
    'Text',
]
