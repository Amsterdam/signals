from datetime import datetime

from django.db import connection

SQL = """
select
    cat.id as category_id,
    cat.parent_id as parent_category_id,
    cat.name as CATEGORIE_NAAM
from public.signals_category as cat
where cat.parent_id is not null;
"""


class CategorieNaam:
    code = "CATEGORIE_NAAM"
    description = "Categorie naam."

    sql = SQL

    def derive(self, begin, end, category, area):
        # Note: for know the following holds
        # - category granularity is per sub category
        # - area granularity is everywhere
        assert isinstance(begin, datetime)
        assert isinstance(end, datetime)

        with connection.cursor() as cursor:
            cursor.execute(self.sql)
            result = cursor.fetchall()
        return result
