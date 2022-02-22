# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
import logging

from django.db import connection
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from signals.apps.api.renderers import SerializedJsonRenderer
from signals.apps.signals import workflow

logger = logging.getLogger(__name__)


class PublicSignalMapViewSet(ViewSet):
    renderer_classes = [SerializedJsonRenderer, BrowsableAPIRenderer]
    # django-drf has too much overhead with these kinds of 'fast' request.
    # When implemented using django-drf, retrieving a large number of elements cost around 4s (profiled)
    # Using pgsql ability to generate geojson, the request time reduces to 30ms (> 130x speedup!)
    # The downside is that this query has to be (potentially) maintained when changing one of the
    # following models: signal, categoryassignment, category, location, status

    def list(self, *args, **kwargs):
        fast_query = f"""
        select jsonb_build_object(
            'type', 'FeatureCollection',
            'features', json_agg(features.feature)
        ) as result from (
            select json_build_object(
                'type', 'Feature',
                'geometry', st_asgeojson(l.geometrie)::jsonb,
                'properties', json_build_object(
                    'id', to_jsonb(s.id),
                    'created_at', to_jsonb(s.created_at),
                    'status', to_jsonb(status.state),
                    'category', json_build_object(
                        'sub', to_jsonb(cat.name),
                        'main', to_jsonb(maincat.name)
                    )
                )
            ) as feature
            from
                signals_signal s
                left join signals_categoryassignment ca on s.category_assignment_id = ca.id
                left join signals_category cat on ca.category_id = cat.id
                left join signals_category maincat on cat.parent_id = maincat.id,
                signals_location l,
                signals_status status
            where
                s.location_id = l.id
                and s.status_id = status.id
                and status.state not in ('{workflow.AFGEHANDELD}', '{workflow.AFGEHANDELD_EXTERN}', '{workflow.GEANNULEERD}', '{workflow.VERZOEK_TOT_HEROPENEN}')
            order by s.id desc
            limit 4000 offset 0
        ) as features
        """ # noqa

        cursor = connection.cursor()
        try:
            cursor.execute(fast_query)
            row = cursor.fetchone()
            return Response(row[0])
        except Exception as e:
            cursor.close
            logger.error('failed to retrieve signals json from db', exc_info=e)

    def get_view_name(self):
        # Overridden to avoid: "Public Signal Map List" that is the default behavior here.
        return 'Public Signal Map'
