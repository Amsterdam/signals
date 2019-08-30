import copy
import datetime
import pprint

from django.contrib.gis.db import models


def get_interval_isoweek(isoyear, isoweek):
    """Get Monday 00:00:00 hours at start of ISO week and the next."""
    monday = f'{isoyear} {isoweek} 1'  # First Monday in ISO week notation
    begin_date = datetime.datetime.strptime(monday, '%G %V %u').date()  # Python >= 3.6

    begin = datetime.datetime.combine(begin_date, datetime.datetime.min.time())
    end = begin + datetime.timedelta(days=7)

    return begin, end


def get_interval_month(year, month):
    """Derive appropriate begin and end of interval for monthly reports."""
    begin = datetime.datetime(year, month, 1, 0, 0, 0)
    if month == 12:
        end = datetime.datetime(year + 1, 1, 1, 0, 0, 0)
    else:
        end = datetime.datetime(year, month, 1, 0, 0, 0)
    return begin, end


class ReportDefinition(models.Model):
    # -- report interval granularity --
    WEEK = 'WEEK'
    MONTH = 'MONTH'  # noqa
    INTERVAL = 'INTERVAL'  # noqa
    INTERVAL_CHOICES = (
        (WEEK, 'Week'),
    )
    # -- report category granularity --
    CATEGORY_ALL = 'CATEGORY_ALL'
    CATEGORY_MAIN = 'CATEGORY_MAIN'  # noqa
    CATEGORY_SUB = 'CATEGORY_SUB'  # noqa
    CATEGORY_CHOICES = (
        (CATEGORY_SUB, 'Subcategorie'),
    )
    # -- report area granularity, currently only whole town --
    AREA_ALL = 'AREA_ALL'
    AREA_STADSDEEL = 'AREA_STADSDEEL'  # noqa
    AREA_WIJK = 'AREA_WIJK'  # noqa
    AREA_BUURT = 'AREA_BUURT'  # noqa
    AREA_CHOICES = (
        (AREA_ALL, 'Overal'),
    )

    # general report stuff
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=1000)

    # granularity of report
    interval = models.CharField(max_length=255, choices=INTERVAL_CHOICES)
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES)
    area = models.CharField(max_length=255, choices=AREA_CHOICES)

    def _get_interval(self, *args, **kwargs):
        """Derive begin and end of interval for report."""
        if self.interval == ReportDefinition.WEEK:
            try:
                isoyear = kwargs['isoyear']
                isoweek = kwargs['isoweek']
            except KeyError:
                msg = 'WEEKly reports need "isoyear" and "isoweek" parameters.'
                raise ValueError(msg)
            else:
                # TODO: add exception checking for bad inputs
                begin, end = get_interval_isoweek(isoyear, isoweek)
        else:
            raise NotImplementedError('Only WEEK interval is supported')

        return begin, end

    def _join_indicators(self, raw_indicators):
        """Join Indicator output."""
        # Current implementation only supports joining on (sub-)category
        index = set()
        empty = {}
        for code, raw_indicator in raw_indicators.items():
            index |= set(row[0] for row in raw_indicator)
            empty[code] = None

        # join data on index variable
        data_dict = {}
        for key in index:
            data_dict[key] = copy.copy(empty)

        for code, raw_indicator in raw_indicators.items():
            for row in raw_indicator:
                category_id, parent_category_id, value = row
                data_dict[category_id][code] = value

        # create a list of dictionaries
        data = []
        for key, indicators in data_dict.items():
            indicators['CATEGORY_ID'] = key
            data.append(indicators)

        return data

    def derive(self, *args, **kwargs):
        """Derive report."""
        begin, end = self._get_interval(*args, **kwargs)

        # No support for category or area granularity choices, currently.
        category = None
        area = None

        # Perform raw calculations / queries to derive the indicators needed for
        # this report.
        raw_results = {}
        for report_indicator in list(self.indicators.all()):
            raw_indicator_output = report_indicator.derive(begin, end, category, area)
            raw_results[report_indicator.code] = raw_indicator_output

        full_report = self._join_indicators(raw_results)
        # pprint.pprint(full_report)

        return full_report
