from signals.apps.dataset.sources.shape import ShapeBoundariesLoader
from signals.apps.signals.models import AreaType


class CBSBoundariesLoader(ShapeBoundariesLoader):
    """
    Load municipal (and neigbhorhood) boundaries as SIA Area instances.
    """
    DATASET_URL = 'https://www.cbs.nl/-/media/cbs/dossiers/nederland-regionaal/wijk-en-buurtstatistieken/wijkbuurtkaart_2019_v1.zip'  # noqa

    # Unfortunately, these filenames are not uniformly named over the years,
    # so a hard-coded mapping is provided for the most recent data file (as of
    # this writing 2019).
    DATASET_INFO = {
        'cbs-gemeente-2019': {
            'shp_file': 'gemeente_2019_v1.shp',
            'code_field': 'GM_CODE',
            'name_field': 'GM_NAAM',
        },
        'cbs-wijk-2019': {
            'shp_file': 'wijk_2019_v1.shp',
            'code_field': 'WK_CODE',
            'name_field': 'WK_NAAM',
        },
        'cbs-buurt-2019': {
            'shp_file': 'buurt_2019_v1.shp',
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
            name=type_string,
            code=type_string,
            description=f'{type_string} from CBS "Wijk- en buurtkaart" data.',
        )

        dataset_info = self.DATASET_INFO[type_string]
        self.data_file = dataset_info['shp_file']
        self.code_field = dataset_info['code_field']
        self.name_field = dataset_info['name_field']
