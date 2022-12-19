# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import logging
from datetime import datetime, timedelta
from time import sleep
from timeit import default_timer as timer

from django.conf import settings
from django.contrib.gis.geos import Point
from django.db import transaction

from signals.apps.gisib import app_settings
from signals.apps.gisib.models import GISIBFeature
from signals.apps.gisib.protocol.filters import Criteria, Filter, Filters
from signals.apps.gisib.protocol.requests import (
    GISIBCollectionDeletedItemsRequest,
    GISIBCollectionWithFilterRequest,
    GISIBLoginRequest
)

logger = logging.getLogger(__name__)


class QuercusTreeLoader:
    _features_created = 0
    _features_updated = 0
    _features_deleted = 0

    login_request = GISIBLoginRequest()
    _bearer_token = None

    @transaction.atomic
    def load(self, time_delta: timedelta = None, purge_table=False) -> None:
        logger.info('Load Oaktrees (Quercus) from GISIB')

        print(settings.FEATURE_FLAGS['GISIB_ENABLED'])
        print('GISIB_ENABLED' in settings.FEATURE_FLAGS)
        print(hasattr(settings.FEATURE_FLAGS, 'GISIB_ENABLED'))
        print(getattr(settings.FEATURE_FLAGS, 'GISIB_ENABLED', False))

        if 'GISIB_ENABLED' in settings.FEATURE_FLAGS and not settings.FEATURE_FLAGS['GISIB_ENABLED']:
            logger.warning('GISIB disabled!')
            return

        self._features_created = 0
        self._features_updated = 0
        self._features_deleted = 0

        start = timer()

        last_run_datetime = datetime.now() - time_delta if time_delta else None
        if last_run_datetime:
            logger.info(f'From date: {last_run_datetime}')

        if purge_table:
            logger.info('Purging the table!')
            GISIBFeature.objects.all().delete()

        self._create_update_features(last_run_datetime=last_run_datetime)
        if last_run_datetime:
            self._delete_features(last_run_datetime=last_run_datetime)

        stop = timer()

        logger.info(f'Created {self._features_created} Features')
        logger.info(f'Updated {self._features_updated} Features')
        logger.info(f'Deleted {self._features_deleted} Features')
        logger.info(f'Time: {stop - start:.2f} second(s)')
        logger.info('Done!')

    @property
    def bearer_token(self) -> str:
        if not self._bearer_token:
            self._bearer_token = self.login_request()
        return self._bearer_token

    def _create_update_features(self, last_run_datetime: datetime = None) -> None:
        request = GISIBCollectionWithFilterRequest(bearer_token=self.bearer_token)

        request_filters = Filters([Filter([Criteria('Soortnaam.Description', 'Quercus', 'StartsWith')])])
        if last_run_datetime:
            request_filters.filters[0].criterias.append(Criteria('LastUpdate',
                                                                 last_run_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                                                                 'GreaterOrEqual'))

        offset = 0
        limit = app_settings.GISIB_LIMIT

        data = request(object_kind_name='Boom', filters=request_filters, offset=offset, limit=limit)
        print(data)
        while data:
            features_in_data_count = len(data['features'])
            logger.debug(f'Got {features_in_data_count} features')

            if features_in_data_count:
                self._import(data=data)

            if features_in_data_count == limit:
                logger.debug('Sleeping 0.5 seconds before the next request')
                sleep(0.5)

                offset += limit
                data = request(object_kind_name='Boom', filters=request_filters, offset=offset, limit=limit)
            else:
                logger.debug('No more features')
                data = False

    def _delete_features(self, last_run_datetime: datetime = None) -> None:
        request = GISIBCollectionDeletedItemsRequest(bearer_token=self.bearer_token)

        data = request(object_kind_name='Boom', reference_date=last_run_datetime.date())
        ids_to_delete = [deleted_feature['Id'] for deleted_feature in data]
        logger.debug(f'Got {len(ids_to_delete)} deleted feature\'s')

        qs = GISIBFeature.objects.filter(gisib_id__in=ids_to_delete)
        logger.debug(f'Found {qs.count()} Features in the database that will be deleted')

        qs.delete()

    def _import(self, data: dict) -> None:
        gisib_features_create = []
        gisib_features_update = []

        for feature in data['features']:
            if feature['properties']['Longitude'] is None or feature['properties']['Latitude'] is None:
                continue

            gisib_feature = GISIBFeature(
                gisib_id=feature['properties']['Id'],
                geometry=Point(float(feature['properties']['Longitude']),
                               float(feature['properties']['Latitude']),
                               srid=4326),
                properties={
                    'object': {
                        'type': feature['properties']['Objecttype']['Description'],
                        'latin': feature['properties']['Soortnaam']['Description'],
                    }
                },
                raw_feature=feature
            )

            if GISIBFeature.objects.filter(
                    gisib_id=feature['properties']['Id'],
                    raw_feature__properties__LastUpdate__lt=feature['properties']['LastUpdate']
            ).exists():
                # Feature exists but has changed in GISIB
                gisib_features_update.append(gisib_feature)
            elif not GISIBFeature.objects.filter(gisib_id=feature['properties']['Id']).exists():
                # Feature does not exists
                gisib_features_create.append(gisib_feature)

        GISIBFeature.objects.bulk_create(gisib_features_create)
        self._features_created += len(gisib_features_create)

        GISIBFeature.objects.bulk_update(gisib_features_update, ['geometry', 'properties', 'raw_feature'])
        self._features_updated += len(gisib_features_update)
