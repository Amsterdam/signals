from datetime import datetime

from django.db import connection

SQL = """
with gauged as
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
            created_at < %(end)s :: timestamp  -- last category update before end of interval
        order by
            "_signal_id" desc) as numbered
    where
        numbered.row_num = 1)
select
    gauged.category_id as category_id,
    null,  -- TODO: remove parent category from indicator output
    count(*) as N_MELDING_NIEUW
from
    gauged
inner join
    public.signals_category as cat
        on cat.id = gauged.category_id
inner join
    public.signals_signal as sig
        on sig.id = gauged._signal_id
where sig.created_at >= %(begin)s :: timestamp -- new signals in interval
    and sig.created_at < %(end)s :: timestamp -- new signals in interval
    and cat.parent_id is not null
group by
    gauged.category_id;
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

        with connection.cursor() as cursor:
            cursor.execute(self.sql, {'begin': begin, 'end': end})
            result = cursor.fetchall()
        return result
