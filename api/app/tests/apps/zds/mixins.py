import os


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
            'zrc_openapi': '/zrc/api/v1/schema/openapi.yaml?v=3',
            'zrc_zaak_create': '/zrc/api/v1/zaken',
            'zrc_zaak_read': '/zrc/api/v1/zaken/',
            'zrc_zaakobject_create': '/zrc/api/v1/zaakobjecten',
            'zrc_status_create': '/zrc/api/v1/statussen',
            'zrc_status_list': '/zrc/api/v1/statussen',
            'drc_openapi': '/drc/api/v1/schema/openapi.yaml?v=3',
            'drc_enkelvoudiginformatieobject_create': '/drc/api/v1/enkelvoudiginformatieobjecten',
            'drc_enkelvoudiginformatieobject_read': '/drc/api/v1/enkelvoudiginformatieobjecten/',
            'drc_objectinformatieobject_create': '/drc/api/v1/objectinformatieobjecten',
            'drc_objectinformatieobject_list': '/drc/api/v1/objectinformatieobjecten',
            'ztc_openapi': '/ztc/api/v1/schema/openapi.yaml?v=3',
            'ztc_statustypen_list': (
                '/ztc/api/v1/catalogussen/8ffb11f0-c7cc-4e35-8a64-a0639aeb8f18/zaaktypen/' +
                'c2f952ca-298e-488c-b1be-a87f11bd5fa2/statustypen'
            ),
            'ztc_statustypen_read': (
                '/ztc/api/v1/catalogussen/8ffb11f0-c7cc-4e35-8a64-a0639aeb8f18/zaaktypen/' +
                'c2f952ca-298e-488c-b1be-a87f11bd5fa2/statustypen/'
            ),
        }

    def get_mock(self, mock, name, status=200, url=None):
        """This is a mock for a GET request.
        This will fetch the needed url and text response by name or
        set this request to a real_http request
        """
        if url is None:
            url = self.urls[name]

        return mock.get(url, text=getattr(self, name), status_code=status)

    def post_mock(self, mock, name, status=201):
        """This is a mock for a POST request.
        This will fetch the needed url and text response by name or
        set this request to a real_http request
        """
        return mock.post(self.urls[name], text=getattr(self, name), status_code=status)

    def post_error_mock(self, mock, name, status=400):
        """This is a mock for a POST error request.
        This will fetch the needed url by name and gets the text via the status that is provided or
        set this request to a real_http request
        """
        return mock.post(
            self.urls[name], text=getattr(self, 'error_{}'.format(status)), status_code=status
        )

    # ZRC ##########################################################################################
    @property
    def zrc_openapi(self):
        with open(os.path.join(self.files_path, 'zrc.yml')) as file:
            return file.read()

    @property
    def zrc_zaak_create(self):
        with open(os.path.join(self.files_path, 'zrc_zaak_create.json')) as file:
            return file.read()

    @property
    def zrc_zaak_read(self):
        with open(os.path.join(self.files_path, 'zrc_zaak_read.json')) as file:
            return file.read()

    @property
    def zrc_zaakobject_create(self):
        with open(os.path.join(self.files_path, 'zrc_zaakobject_create.json')) as file:
            return file.read()

    @property
    def zrc_status_create(self):
        with open(os.path.join(self.files_path, 'zrc_status_create.json')) as file:
            return file.read()

    @property
    def zrc_status_list(self):
        with open(os.path.join(self.files_path, 'zrc_status_list.json')) as file:
            return file.read()

    # DRC ##########################################################################################
    @property
    def drc_openapi(self):
        with open(os.path.join(self.files_path, 'drc.yml')) as file:
            return file.read()

    @property
    def drc_enkelvoudiginformatieobject_create(self):
        path = os.path.join(self.files_path, 'drc_enkelvoudiginformatieobject_create.json')
        with open(path) as file:
            return file.read()

    @property
    def drc_enkelvoudiginformatieobject_read(self):
        path = os.path.join(self.files_path, 'drc_enkelvoudiginformatieobject_read.json')
        with open(path) as file:
            return file.read()

    @property
    def drc_objectinformatieobject_create(self):
        with open(os.path.join(self.files_path, 'drc_objectinformatieobject_create.json')) as file:
            return file.read()

    @property
    def drc_objectinformatieobject_list(self):
        with open(os.path.join(self.files_path, 'drc_objectinformatieobject_list.json')) as file:
            return file.read()

    # ZTC ##########################################################################################
    @property
    def ztc_openapi(self):
        with open(os.path.join(self.files_path, 'ztc.yml')) as file:
            return file.read()

    @property
    def ztc_statustypen_list(self):
        with open(os.path.join(self.files_path, 'ztc_statustypen_list.json')) as file:
            return file.read()

    @property
    def ztc_statustypen_read(self):
        with open(os.path.join(self.files_path, 'ztc_statustypen_read.json')) as file:
            return file.read()

    # ERRORS #######################################################################################
    @property
    def error_400(self):
        with open(os.path.join(self.files_path, '400.json')) as file:
            return file.read()

    # HELPERS ######################################################################################
    @property
    def ztc_statusses(self):
        with open(os.path.join(self.files_path, 'ztc_statusses.json')) as file:
            return file.read()

    @property
    def drc_images(self):
        with open(os.path.join(self.files_path, 'drc_images.json')) as file:
            return file.read()
