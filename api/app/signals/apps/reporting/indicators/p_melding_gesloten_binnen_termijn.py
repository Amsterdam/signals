import pprint

from datetime import datetime

from django.db import connection

SQL = """
with closed_signals_in_window as (select
    sig.id as _signal_id,
    sig.created_at as signal_created_at,
    cat.id as category_id,
    status.created_at as status_created_at,
    status.state as status_state,
    case
        when slo.use_calendar_days = true then sig.created_at + slo.n_days * '24 hours' :: interval
        else
            case
                when extract(dow from sig.created_at + slo.work_day_interval) = 0 -- sunday, add one day
                    then sig.created_at + slo.work_day_interval + '24 hours' :: interval
                when extract(dow from sig.created_at + slo.work_day_interval) = 6 -- saturday, add two days
                    then sig.created_at + slo.work_day_interval + 2 * '24 hours' :: interval
                else sig.created_at + slo.work_day_interval
            end
    end as deadline
from public.signals_signal as sig
inner join (
    select
        _signal_id,
        category_id as "id"
    from (
        select
            _signal_id,
            category_id,
            row_number() over(partition by _signal_id order by created_at desc) as row_n
        from
            public.signals_categoryassignment
        where
            created_at < %(end)s :: timestamp
        ) as gauged_cas
    where
        gauged_cas.row_n = 1
    ) as cat  -- category assignment gauged at end of interval we are interested in
        on cat._signal_id = sig.id
inner join (
    select
        _signal_id,
        state,
        created_at
    from (
        select
            _signal_id,
            state,
            created_at,
            row_number() over (partition by _signal_id order by created_at desc) as row_n
        from
            public.signals_status
        where
            state in ('o', 'a')  -- states "afgehandeld", "geannuleerd"
            and created_at >= %(begin)s :: timestamp
            and created_at < %(end)s :: timestamp
        ) as gauged_status
        where
            gauged_status.row_n = 1
    ) as status
        on status._signal_id = sig.id
inner join (
    select
        *,
        ((slo.n_days / 5) * 7 + slo.n_days %% 5) * '24 hours' :: interval as work_day_interval -- PAS OP
    from
        public.signals_servicelevelobjective as slo
) as slo
    on slo.category_id = cat.id
order by
    sig.created_at desc) -- end of closed_signals_in_window query -- start counting below:
select
    category_id,
    case
        when count(*) = 0 then 0
        else
            round(100 * sum(case when status_created_at <= deadline then 1 else 0 end) :: float / count(*)) :: integer
    end as P_MELDING_GESLOTEN_BINNEN_TERMIJ
from
    closed_signals_in_window
group by
    category_id;
"""


class PMeldingGeslotenBinnenTermijn:
    code = "P_MELDING_GESLOTEN_BINNEN_TERMIJ"
    description = "Percentage meldingen afgehandeld binnen termijn in gegeven periode."
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
        }
        with connection.cursor() as cursor:
            cursor.execute(self.sql, db_query_parameters)
            result = cursor.fetchall()

        pprint.pprint(result)

        return result
