# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from signals.apps.dataset.sources.shape import ShapeBoundariesLoader
from signals.apps.signals.models import AreaType


class CBSBoundariesLoader(ShapeBoundariesLoader):
    """
    Load municipal (and neigbhorhood) boundaries as SIA Area instances.
    """
    DATASET_URL = 'https://www.cbs.nl/-/media/cbs/dossiers/nederland-regionaal/wijk-en-buurtstatistieken/wijkbuurtkaart_2021_v1.zip'  # noqa
    # Unfortunately, these filenames are not uniformly named over the years,
    # so a hard-coded mapping is provided for the most recent data file (as of
    # this writing 2019).
    DATASET_INFO = {
        'cbs-gemeente-2021': {
            'shp_file': 'WijkBuurtkaart_2021_v1/gemeente_2021_v1.shp',
            'code_field': 'GM_CODE',
            'name_field': 'GM_NAAM',
        },
        'cbs-wijk-2021': {
            'shp_file': 'WijkBuurtkaart_2021_v1/wijk_2021_v1.shp',
            'code_field': 'WK_CODE',
            'name_field': 'WK_NAAM',
        },
        'cbs-buurt-2021': {
            'shp_file': 'WijkBuurtkaart_2021_v1/buurt_2021_v1.shp',
            'code_field': 'BU_CODE',
            'name_field': 'BU_NAAM',
        }
    }

    PROVIDES = DATASET_INFO.keys()

    def __init__(self, **options):
        type_string = options['type_string']
        # Data downloaded / processed here. Caller is responsible to clean-up directory.
        self.directory = options['dir']

        assert type_string in self.PROVIDES

        self.area_type, _ = AreaType.objects.get_or_create(
            code=type_string,
            defaults={'name': type_string, 'description': f'{type_string} from CBS "Wijk- en buurtkaart" data.'}
        )

        dataset_info = self.DATASET_INFO[type_string]
        self.data_file = dataset_info['shp_file']
        self.code_field = dataset_info['code_field']
        self.name_field = dataset_info['name_field']
