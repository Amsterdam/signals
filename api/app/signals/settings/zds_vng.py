"""
This file should never be used in STAGING and PRODUCTION.

This file is used to test the code against the Reference implementation from VNG

There are credentials in this file. The credentials are here so they won't have to be requested
for every user. The credentials can be requested freely via this url.
https://ref.tst.vng.cloud/tokens/
That is why the credentials are not hidden. There is no need todo so.

If you want to test against the Reference implementation create a local.py file in the settings
and add 'from .zds_vng import *'. Never place this in any other settings file.
"""

#
# Zaken settings
#
ZDS_BASE_PATH = '/{}/api/v1/'
RSIN_NUMBER = '002564440'
HOST_URL = 'https://example.com'


# ZTC settings
ZTC_HOST = 'ref.tst.vng.cloud'
ZTC_PORT = '443'
ZTC_SCHEME = 'https'
ZTC_AUTH = {
    'client_id': 'mor-amsterdam-xyOyIP54BudG',
    'secret': 'gdnsnNqEeDJWiDNExiSvabvOHo2KmHs9',
    'scopes': [
        'zds.scopes.zaaktypes.lezen',
    ]
}
ZTC_CATALOGUS_ID = '8ffb11f0-c7cc-4e35-8a64-a0639aeb8f18'
ZTC_ZAAKTYPE_ID = 'c2f952ca-298e-488c-b1be-a87f11bd5fa2'
ZTC_INFORMATIEOBJECTTYPE_ID = '5ab00303-1b58-4668-b054-595c0635596c'
ZTC_APPENDED_PATH = '/ztc'

ZTC_URL = "{}://{}{}".format(ZTC_SCHEME, ZTC_HOST, ZTC_APPENDED_PATH)

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
ZRC_HOST = 'ref.tst.vng.cloud'
ZRC_PORT = '443'
ZRC_SCHEME = 'https'
ZRC_AUTH = {
    'client_id': 'mor-amsterdam-xyOyIP54BudG',
    'secret': 'gdnsnNqEeDJWiDNExiSvabvOHo2KmHs9',
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
DRC_HOST = 'ref.tst.vng.cloud'
DRC_PORT = '443'
DRC_SCHEME = 'https'
DRC_AUTH = {
    'client_id': 'mor-amsterdam-xyOyIP54BudG',
    'secret': 'gdnsnNqEeDJWiDNExiSvabvOHo2KmHs9',
    'scopes': []
}

DRC_URL = "{}://{}:{}".format(DRC_SCHEME, DRC_HOST, DRC_PORT)
