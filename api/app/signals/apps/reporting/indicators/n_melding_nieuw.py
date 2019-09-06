from datetime import datetime

from django.db import connection

SQL = """
with gauged_cat as
    (select
        _signal_id,
        category_id
    from
        (select
            _signal_id,
            category_id,
            row_number() over(partition by _signal_id order by created_at desc) as row_num
        from
            public.signals_categoryassignment
        where
            created_at >= %(begin)s :: timestamp  -- only signals created in this interval
            and created_at < %(end)s :: timestamp
        ) as numbered
    where
        numbered.row_num = 1)  -- last category update before end of interval
select
    gauged_cat.category_id as category_id,
    count(*) as N_MELDING_NIEUW
from
    gauged_cat
inner join
    public.signals_category as cat
        on cat.id = gauged_cat.category_id
inner join
    public.signals_signal as sig
        on sig.id = gauged_cat._signal_id
where sig.created_at >= %(begin)s :: timestamp -- new signals in interval
    and sig.created_at < %(end)s :: timestamp
    and cat.parent_id is not null
group by
    gauged_cat.category_id;
"""


class NMeldingNieuw:
    code = "N_MELDING_NIEUW"
    description = "Aantal nieuwe meldingen in een gegeven periode."
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
