from django.db.models import Q
from django.utils import timezone

from signals.apps.email_integrations.core.utils import is_business_hour
from signals.apps.signals.models import STADSDEEL_NIEUWWEST, Category, Signal


def is_signal_applicable(signal: Signal) -> bool:
    """Is given `Signal` applicable for VTH Nieuw West.

    :param signal: Signal object
    :returns: bool
    """
    # We're only sending notification e-mails when the current Dutch time is outside
    # business / working hours.
    current_dutch_time = timezone.localtime(timezone.now()).time()
    if is_business_hour(current_dutch_time):
        return False

    if signal.location.stadsdeel != STADSDEEL_NIEUWWEST:
        return False

    eligible_categories = Category.objects.filter(
        Q(parent__slug='overlast-bedrijven-en-horeca') & (
            Q(slug='geluidsoverlast-muziek') |
            Q(slug='geluidsoverlast-installaties') |
            Q(slug='overlast-terrassen') |
            Q(slug='stankoverlast') |
            Q(slug='overlast-door-bezoekers-niet-op-terras')))

    return signal.category_assignment.category in eligible_categories
