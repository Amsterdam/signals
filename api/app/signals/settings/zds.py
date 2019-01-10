import os

#
# Zaken settings
#
ZDS_BASE_PATH = '/api/v1/'
RSIN_NUMBER = '002564440'

# ZTC settings
# TODO: This needs to contain the correct settings for the staging environment Amsterdam.
ZTC_HOST = os.getenv('ZTC_HOST')
ZTC_PORT = os.getenv('ZTC_PORT')
ZTC_SCHEME = os.getenv('ZTC_SCHEME', 'https')
ZTC_AUTH = {
    'client_id': os.getenv('ZTC_CLIENT_ID'),
    'secret': os.getenv('ZTC_CLIENT_SECRET'),
    'scopes': [
        'zds.scopes.zaaktypes.lezen',
    ]
}
ZTC_CATALOGUS_ID = os.getenv('ZTC_CATALOGUS_ID')
ZTC_ZAAKTYPE_ID = os.getenv('ZTC_ZAAKTYPE_ID')
ZTC_INFORMATIEOBJECTTYPE_ID = os.getenv('ZTC_INFORMATIEOBJECTTYPE_ID')
ZTC_APPENDED_PATH = ''

ZTC_URL = "{}://{}{}".format(ZTC_SCHEME, ZTC_HOST, ZTC_APPENDED_PATH)
HOST_URL = 'https://acc.meldingen.amsterdam.nl'
ZTC_CATALOGUS_URL = '{ztc_url}/api/v1/catalogussen/{catalogus_id}'.format(
    ztc_url=ZTC_URL, catalogus_id=ZTC_CATALOGUS_ID
)
ZTC_ZAAKTYPE_URL = '{catalogus_url}/zaaktypen/{zaaktype_id}'.format(
    catalogus_url=ZTC_CATALOGUS_URL, zaaktype_id=ZTC_ZAAKTYPE_ID,
)
ZTC_INFORMATIEOBJECTTYPE_URL = '{catalogus_url}/informatieobjecttypen/{informatietype_id}'.format(
    catalogus_url=ZTC_CATALOGUS_URL, informatietype_id=ZTC_INFORMATIEOBJECTTYPE_ID,
)

# ZRC settings
# TODO: This needs to contain the correct settings for the staging environment Amsterdam.
ZRC_HOST = os.getenv('ZRC_HOST')
ZRC_PORT = os.getenv('ZRC_PORT')
ZRC_SCHEME = os.getenv('ZRC_SCHEME', 'https')
ZRC_AUTH = {
    'client_id': os.getenv('ZRC_CLIENT_ID'),
    'secret': os.getenv('ZRC_CLIENT_SECRET'),
    'scopes': [
        'zds.scopes.zaken.aanmaken',
        'zds.scopes.statussen.toevoegen',
        'zds.scopes.zaken.lezen',
        'zds.scopes.zaaktypes.lezen',
    ],
    'zaaktypes': [
        ZTC_ZAAKTYPE_URL
    ]
}

ZRC_URL = "{}://{}:{}".format(ZRC_SCHEME, ZRC_HOST, ZRC_PORT)
ZRC_ZAAKOBJECT_TYPE = 'MeldingOpenbareRuimte'

# DRC settings
# TODO: This needs to contain the correct settings for the staging environment Amsterdam.
DRC_HOST = os.getenv('DRC_HOST')  # should be a staging domain.
DRC_PORT = os.getenv('DRC_PORT')
DRC_SCHEME = os.getenv('DRC_SCHEME', 'https')
DRC_AUTH = {
    'client_id': os.getenv('DRC_CLIENT_ID'),
    'secret': os.getenv('DRC_CLIENT_SECRET'),
    'scopes': []
}

DRC_URL = "{}://{}:{}".format(DRC_SCHEME, DRC_HOST, DRC_PORT)
