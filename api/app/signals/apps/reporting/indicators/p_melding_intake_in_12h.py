from datetime import datetime

from django.db import connection

SQL = """
select
	category_id,
	case
		when count(*) = 0 then 0
		else round(100 *(sum(in_time) ::float / count(*))) :: integer
	end as P_MELDING_INTAKE_IN_12H
from ( 
	select
		category_id, 
		case when (sub.created_at - sub.lag_1_created_at < '12 hours' :: interval) then 1 else 0 end as in_time -- 0 false, 1 true for sum()  # noqa
	from(
		select
			_signal_id,
			created_at,
			lag(created_at) over(partition by _signal_id order by created_at asc) as lag_1_created_at,  -- # noqa
			row_number() over(partition by _signal_id order by created_at asc) as row_num
		from 
			public.signals_status
		where
		    created_at >= %(begin)s :: timestamp
		    and created_at < %(end)s :: timestamp + '12 hours' :: interval
		) as sub  
	inner join
		public.signals_categoryassignment as cas
			on cas._signal_id = sub._signal_id
	where
		sub.row_num = 2) as per_category_in_time
inner join
	public.signals_category as cat
		on cat.id = category_id
where
	cat.parent_id is not null
group by
	category_id;
"""


class PMeldingIntakeIn12H:
    code = "P_MELDING_INTAKE_IN_12H"
    description = "Percentage meldingen opgepakt binnen 12 uur."
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