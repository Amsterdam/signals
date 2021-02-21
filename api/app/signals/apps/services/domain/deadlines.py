"""
Calculate deadline for solving complaints.

- supports calculations in working days or just normal calendar days
- supports scaling a deadline with an arbitrary factor (used to find complaints
  that overrun their deadline by a factor of 3)
- workdays are defined as Monday through Friday, ignoring festivities
"""
from datetime import datetime, time, timedelta


class DeadlineCalculationService:
    @staticmethod
    def get_start(created_at):
        # When promise to complainant is given in working days and the complaint
        # received during the weekend, work will only start on Monday. The
        # deadline calculation needs to take this into account.
        weekday = created_at.date().weekday()

        if weekday > 4:
            return datetime.combine(created_at.date(), time(0, 0, 0)) + timedelta(days=7-weekday)
        return created_at

    @staticmethod
    def get_end(start, n_days, factor):
        # When promise to complainant is given in working days we cannot just add
        # the number of working days to the day the complaint was received. Non-
        # working days need to be taken into account.

        # Note in normal operation this function is never called with a weekend
        # day (see the get_deadline method for why that is the case).
        n_days = n_days * factor
        n_weeks, days_remaining = divmod(n_days, 5)  # 5 days per workweek

        deadline_weekday = start.date().weekday() + days_remaining
        if deadline_weekday > 4:
            # Deadline would fall in weekend and we have to shift by 2 extra days
            return start + timedelta(days=(n_weeks * 7) + days_remaining + 2)
        return start + timedelta(days=(n_weeks * 7) + days_remaining)

    @staticmethod
    def get_deadline(created_at, n_days, use_calendar_days, factor=1):
        if use_calendar_days:
            return created_at + timedelta(days=(n_days * factor))
        start = DeadlineCalculationService.get_start(created_at)
        deadline = DeadlineCalculationService.get_end(start, n_days, factor)

        return deadline
