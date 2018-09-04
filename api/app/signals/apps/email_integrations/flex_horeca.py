import logging

from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.template import loader
from django.utils import timezone

from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)


def send_mail(pk):
    """Send e-mail to Flex Horeca Team when applicable.

    :param pk: Signal object id
    :returns:
    """
    try:
        signal = Signal.objects.get(id=pk)
    except Signal.DoesNotExist as e:
        logger.exception(str(e))
        return

    if _is_signal_applicable(signal):
        template = loader.get_template('email/mail_flex_horeca.txt')
        context = {'signal': signal, }
        message = template.render(context)
        django_send_mail(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=message,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_FLEX_HORECA_INTEGRATION_ADDRESS,),
            fail_silently=False)


def _is_signal_applicable(signal):
    """Is given `Signal` applicable for Flex Horeca Team.

    Flex Horeca Team can't check the Signals Dashboard on friday and
    saterday. That's why we send them an e-mail notification on these days
    for new `Signal` objects that are created.

    :param signal: Signal object
    :returns: bool
    """
    today = timezone.now()
    weekday = today.isoweekday()
    is_friday_or_saterday = weekday == 5 or weekday == 6
    if not is_friday_or_saterday:
        return False

    eligible_main_categories = 'Overlast Bedrijven en Horeca'
    eligible_sub_categories = (
        'Geluidsoverlast muziek',
        'Geluidsoverlast installaties',
        'Overlast terrassen',
        'Stankoverlast')
    is_applicable_for_flex_horeca = (
            signal.category.main == eligible_main_categories
            and signal.category.sub in eligible_sub_categories)

    return is_applicable_for_flex_horeca
