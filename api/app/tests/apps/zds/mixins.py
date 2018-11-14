import os

from django.conf import settings


class ZDSMockMixin(object):
    """This will help with writing mocks for the ZDS compoments.

    It has a dict of all the available urls. The keys of the urls should match a property with the
    same name.

    The only functions that should be used are:
    get_mock()
    post_mock()
    post_error_mock()
    """
    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.files_path = os.path.join(self.dir_path, 'files')

        self.urls = {
            'zrc_openapi': '{}/api/v1/schema/openapi.yaml'.format(settings.ZRC_URL),
            'zrc_zaak_create': '{}/api/v1/zaken'.format(settings.ZRC_URL),
            'zrc_zaakobject_create': '{}/api/v1/zaakobjecten'.format(settings.ZRC_URL),
            'zrc_status_create': '{}/api/v1/statussen'.format(settings.ZRC_URL),
            'drc_openapi': '{}/api/v1/schema/openapi.yaml'.format(settings.DRC_URL),
            'drc_enkelvoudiginformatieobject_create': (
                '{}/api/v1/enkelvoudiginformatieobjecten'.format(settings.DRC_URL)
            ),
            'drc_objectinformatieobject_create': (
                '{}/api/v1/objectinformatieobjecten'.format(settings.DRC_URL)
            ),
            'ztc_openapi': '{}/api/v1/schema/openapi.yaml'.format(settings.ZTC_URL),
        }

    def get_mock(self, mock, name, status=200):
        """This is a mock for a GET request.
        This will fetch the needed url and text response by name or
        set this request to a real_http request
        """
        if settings.ZDS_TESTING_MOCK:
            return mock.get(self.urls[name], text=getattr(self, name), status_code=status)
        return mock.get(self.urls[name], real_http=True)

    def post_mock(self, mock, name, status=201):
        """This is a mock for a POST request.
        This will fetch the needed url and text response by name or
        set this request to a real_http request
        """
        if settings.ZDS_TESTING_MOCK:
            return mock.post(self.urls[name], text=getattr(self, name), status_code=status)
        return mock.post(self.urls[name], real_http=True)

    def post_error_mock(self, mock, name, status=400):
        """This is a mock for a POST error request.
        This will fetch the needed url by name and gets the text via the status that is provided or
        set this request to a real_http request
        """
        if settings.ZDS_TESTING_MOCK:
            return mock.post(
                self.urls[name],
                text=getattr(self, 'error_{}'.format(status)),
                status_code=status
            )
        return mock.post(self.urls[name], real_http=True)

    # ZRC ##########################################################################################
    @property
    def zrc_openapi(self):
        with open(os.path.join(self.files_path, 'zrc.yaml')) as file:
            return file.read()

    @property
    def zrc_zaak_create(self):
        with open(os.path.join(self.files_path, 'zrc_zaak_create.json')) as file:
            return file.read()

    @property
    def zrc_zaakobject_create(self):
        with open(os.path.join(self.files_path, 'zrc_zaakobject_create.json')) as file:
            return file.read()

    @property
    def zrc_status_create(self):
        with open(os.path.join(self.files_path, 'zrc_status_create.json')) as file:
            return file.read()

    # DRC ##########################################################################################
    @property
    def drc_openapi(self):
        with open(os.path.join(self.files_path, 'drc.yaml')) as file:
            return file.read()

    @property
    def drc_enkelvoudiginformatieobject_create(self):
        path = os.path.join(self.files_path, 'drc_enkelvoudiginformatieobject_create.json')
        with open(path) as file:
            return file.read()

    @property
    def drc_objectinformatieobject_create(self):
        with open(os.path.join(self.files_path, 'drc_objectinformatieobject_create.json')) as file:
            return file.read()

    # ZTC ##########################################################################################

    # ERRORS #######################################################################################
    @property
    def error_400(self):
        with open(os.path.join(self.files_path, '400.json')) as file:
            return file.read()
