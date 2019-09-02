from datetime import datetime

from django.db import connection

SQL = """
select
    cat.slug,
    count(feedback.submitted_at),
    round(
        count(case when feedback.is_satisfied = true then true else null end) :: float 
        / count(feedback.submitted_at) :: float
        * 100
    ) :: int as P_MELDING_TEVREDEN
from
    public.feedback_feedback as feedback
    inner join public.signals_signal as sig
        on feedback."_signal_id" = sig.id
    inner join public.signals_categoryassignment as cas
        on sig.category_assignment_id = cas.id
    inner join public.signals_category as cat
        on cat.id = cas.category_id
where feedback.submitted_at >= %(begin)s :: timestamp
    and feedback.submitted_at < %(end)s :: timestamp
    and cat.parent_id is not null
group by cat.id;
"""


class PMeldingTevreden:
    code = "P_MELDING_TEVREDEN"
    description = "Percentage van ontvangen feedback van tevreden melders."

    sql = SQL

    def derive(self, begin, end, category, area):
        # Note: for know the following holds
        # - category granularity is per sub category
        # - area granularity is everywhere
        assert isinstance(begin, datetime)
        assert isinstance(end, datetime)

        with connection.cursor() as cursor:
            cursor.execute(self.sql, {'begin': begin, 'end': end})
            result = cursor.fetchall()
        return result
