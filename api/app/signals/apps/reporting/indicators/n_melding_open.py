from datetime import datetime

from django.db import connection

# TODO: Investigate JSON straight from Postgres (?)

# Note: it is anticipated that several chunks of SQL will be needed in the
# general case to support all category and area subdivisions. For now we only
# support parametrized intervals and always group by sub category.
SQL = """
select
    cat.id as category_id,
    cat.parent_id as parent_category_id,
    count(*) as N_MELDING_OPEN
from
    (select
        sorted._signal_id as signal_id,
        sorted.created_at as created_at,
        sorted.state as state,
        lag(sorted._signal_id, 1) over () as next_signal_id
    from
        (select
            id,
            _signal_id,
            created_at,
            state
        from public.signals_status as stat
        where stat.created_at < %(end)s :: timestamp
        order by
            "_signal_id" desc,
            created_at desc) as sorted
    ) as with_lead
inner join public.signals_signal as sig
    on sig.id = with_lead.signal_id
inner join public.signals_categoryassignment as cas
    on sig.category_assignment_id = cas.id
inner join public.signals_category as cat
    on cas.category_id = cat.id
inner join public.signals_category as parent_cat
    on parent_cat.id = cat.parent_id
where
    with_lead.signal_id != with_lead.next_signal_id
and
    with_lead.state not in ('o', 'a', 's')
and
    cat.parent_id is not null
group by cat.id;
"""


class NMeldingOpen:
    code = "N_MELDING_OPEN"
    description = "Aantal open meldingen aan het eind van gegeven periode."

    sql = SQL

    def derive(self, begin, end, category, area):
        # Note: for know the following holds
        # - category granularity is per sub category
        # - area granularity is everywhere
        assert isinstance(begin, datetime)
        assert isinstance(end, datetime)

        with connection.cursor() as cursor:
            cursor.execute(self.sql, {'end': end})
            result = cursor.fetchall()
        return result
