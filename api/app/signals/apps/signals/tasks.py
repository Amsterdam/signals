import logging

from signals.apps.signals.models.category_translation import CategoryTranslation
from signals.apps.signals.models.signal import Signal
from signals.celery import app

logger = logging.getLogger(__name__)


@app.task
def translate_category(signal_id):
    signal = Signal.objects.get(pk=signal_id)

    current_category = signal.category_assignment.category
    try:
        trans = CategoryTranslation.objects.get(old_category=current_category)
    except CategoryTranslation.DoesNotExist:
        return  # no need to perform a category re-assignment

    data = {
        'category': trans.new_category,
        'text': trans.text,
        'created_by': None,  # This wil show as "SIA systeem"
    }

    Signal.actions.update_category_assignment(data, signal)
