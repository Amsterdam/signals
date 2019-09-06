from datetime import datetime

from django.db import connection

SQL = """
select
    gauged_cas.category_id as category_id,
    case
        when count(*) = 0 then 0
    else round(100 * sum(case when feedback.is_satisfied is true then 1 else 0  end) ::  float / count(*)) :: integer  --  # noqa
    end as P_MELDING_TEVREDEN
from
    public.feedback_feedback as feedback
inner join (
    select
        _signal_id,
        category_id
    from (
        select
            _signal_id,
            category_id,
            row_number() over(partition by _signal_id order by created_at desc) as row_num
        from
            public.signals_categoryassignment
        where
            created_at < %(end)s :: timestamp) as numbered
    where
        numbered.row_num = 1) as gauged_cas
        on gauged_cas._signal_id = feedback._signal_id
inner join
    public.signals_category as cat
        on gauged_cas.category_id = cat.id
where
    feedback.submitted_at >= %(begin)s
    and feedback.submitted_at < %(end)s  -- this also gets rid of feedback.submitted_at is null entries
    and cat.parent_id is not null
group by gauged_cas.category_id;
"""


class PMeldingTevreden:
    code = "P_MELDING_TEVREDEN"
    description = "Percentage van ontvangen feedback van tevreden melders."
    no_result = 0

    sql = SQL

    def derive(self, begin, end, category, area):
        # Note: for know the following holds
        # - category granularity is per sub category
        # - area granularity is everywhere
        assert isinstance(begin, datetime)
        assert isinstance(end, datetime)

        db_query_parameters = {
            'begin': begin,
            'end': end,
            'category': category,
            'area': area,
        }
        with connection.cursor() as cursor:
            cursor.execute(self.sql, db_query_parameters)
            result = cursor.fetchall()
        return result
