import logging


from signals.apps.signals.models.category_translation import CategoryTranslation
from signals.apps.signals.models.signal import Signal
from signals.celery import app
from signals.utils.datawarehouse import save_csv_files_datawarehouse

logger = logging.getLogger(__name__)


@app.task
def task_save_csv_files_datawarehouse():
    """Celery task to save CSV files for Datawarehouse.

    This task is scheduled in Celery beat to run periodically.

    :returns:
    """
    save_csv_files_datawarehouse()


@app.task
def translate_category(signal_id):
    # TODO: Check whether we really want this as a celery task
    signal = Signal.objects.get(pk=signal_id)

    current_category = signal.category_assignmen.category
    try:
        trans = CategoryTranslation.objects.get(old_category=current_category).first()
    except CategoryTranslation.DoesNotExist:
        return  # no need to perform a category re-assignment

    data = {
        'category': trans.new_category,
        'text': trans.text,
        'created_by': None,  # This wil show as "SIA systeem"
    }

    signal.actions.update_category_assignment(data, signal)
