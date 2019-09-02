from datetime import datetime

from django.db import connection

SQL = """
select
    category_id,
    parent_category_id,
    case 
        when sub.n_submitted = 0 then 0 
        else round(100 * (sub.n_satisfied :: float) / sub.n_submitted) :: integer
    end as P_MELDING_TEVREDEN
from (
    select
        cat.id as category_id,
        cat.parent_id as parent_category_id,
        count(feedback.submitted_at) as n_submitted,
        sum(case when feedback.is_satisfied then 1 else 0 end) as n_satisfied
    from
        public.feedback_feedback as feedback
        inner join public.signals_signal as sig
            on feedback."_signal_id" = sig.id
        inner join public.signals_categoryassignment as cas
            on sig.category_assignment_id = cas.id
        inner join public.signals_category as cat
            on cat.id = cas.category_id
    where cat.parent_id is not null
    group by cat.id
) as sub
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
