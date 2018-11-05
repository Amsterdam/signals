# Table of contents:
- [Documentatie](#documentatie)
- [Mapping](#mapping)
    - [ZRC](#zrc)
    - [DRC](#drc)
- [Voorgestelde veranderingen](#voorgestelde-veranderingen)
    - [Wijzigingen in SIA](#wijzigingen-in-sia)
    - [Status lijst](#status-lijst)
    - [Ophalen van de Zaak gegevens](#ophalen-van-de-zaak-gegevens)
    - [Ophalen van de Document gegevens](#ophalen-van-de-document-gegevens)
- [Authenticatie op de ZRC, DRC en ZTC endpoints](#authenticatie-op-de-zrc-drc-en-ztc-endpoints)

# Documentatie
[De algemene documentatie](https://ref.tst.vng.cloud/)

[ZRC api spec](https://ref.tst.vng.cloud/zrc/api/v1/schema/)

[DRC api spec](https://ref.tst.vng.cloud/drc/api/v1/schema/)

[ZTC api spec](https://ref.tst.vng.cloud/ztc/api/v1/schema/)

[Integration tests](https://github.com/VNG-Realisatie/gemma-zaken-test-integratie/blob/master/tests/test_userstory_39.py)

[Gemma ZDS client](https://github.com/VNG-Realisatie/gemma-zds-client)

[ZDS Changelog](https://github.com/VNG-Realisatie/gemma-zaakregistratiecomponent/blob/develop/CHANGELOG.rst)

# Mapping
Hieronder komt de eerste opzet die gemaakt is voor het overzetten van de data van SIA naar
het zaaksysteem (omvattend voor het ZRC, DRC en ZTC)
Alles zal gebaseerd worden op de create calls die gedaan moeten worden.

## ZRC
Hierin zal de grootste verandering plaats vinden. Aangezien elke melding een zaak is.
Het zal gesplitst worden per model in het ZRC.

| Zaak                          | SIA                   | Beperkingen           |           |
|-------------------------------|-----------------------|-----------------------|-----------|
| identificatie                 | (signal_uuid)         | <= 40 characters      |           |
| bronorganisatie               |                       | [1..9] characters     | Required  |
| omschrijving                  |                       | <= 80 characters      |           |
| zaaktype                      |                       | [1..200] characters   | Required  |
| registratiedatum              | created_at            | -                     |           |
| verantwoordelijkeOrganisatie  |                       | [1..200] characters   | Required  |
| startdatum                    | incident_date_start   | -                     | Required  |
| einddatum                     | incident_date_end     | -                     |           |
| einddatumGepland              | operational_date      | -                     |           |
| uiterlijkeEinddatumAfdoening  | expire_date           | -                     |           |
| toelichting                   |                       | <= 1000 characters    |           |
| zaakgeometrie                 |                       | -                     |           |
| kenmerken                     |                       | -                     |           |

Om de status te koppelen moeten we een status aanmaken. Voor elke status update moet dit gebeuren.
Hierdoor krijg je een geschiedenis van statussen die afgelopen wordt.

| Statussen             | SIA           | Beperkingen               |           |
|-----------------------|---------------|---------------------------|-----------|
| zaak                  |               | -                         | required  |
| statusType            | state         | [ 1 .. 200 ] characters   | required  |
| datumStatusGezet      | created_at    | -                         | required  |
| statustoelichting     | text          | <= 1000 characters        |           |

Dit is een koppeling tussen een zaak een signaal (waar extra informatie te vinden is).

| Zaakobject            | SIA           | Beperkingen               |           |
|-----------------------|---------------|---------------------------|-----------|
| zaak                  |               | -                         | required  |
| object                | URL naar SIA  | [ 1 .. 200 ] characters   | required  |
| relatieomschrijving   |               | <= 80 characters          |           |
| type                  |               | ENUM                      | required  |


## DRC
De Foto die wordt geüpload zal verplaatst moeten worden van de SIA applicatie naar het DRC.

| Enkelvoudiginformatieobject | SIA                   | Beperkingen           |           |
|-----------------------------|-----------------------|-----------------------|-----------|
| identificatie               |                       | <= 40 characters      |           |
| bronorganisatie             |                       | <= 9 characters       |           |
| creatiedatum                |                       | -                     | required  |
| titel                       | document name?        | [1..200] characters   | required  |
| vertrouwelijkaanduiding     |                       | -                     |           |
| auteur                      | uploader?             | [1..200] characters   | required  |
| formaat                     |                       | <= 255 characters     |           |
| taal                        |                       | ENUM                  | required  |
| inhoud                      |                       | -                     |           |
| link                        | image                 | <= 200 characters     |           |
| beschrijving                |                       | <= 1000 characters    |           |
| informatieobjecttype        |                       | [1..200] characters   | required  |

Er moet denk ik ook iets gebeuren op het objectinformatieobject. Alleen is mij niet meteen
duidelijk wat er zou moeten gebeuren en waar het voor dient

| objectinformatieobject | SIA                   | Beperkingen           |           |
|------------------------|-----------------------|-----------------------|-----------|
| informatieobject       |                       | -                     | required  |
| object                 | link naar de zaak     | [1..200] characters   | required  |
| objectType             | zaak/besluit          | ENUM                  | required  |
| titel                  |                       | <= 200 characters     |           |
| beschrijving           |                       | <= 1000 characters    |           |
| registratiedatum       |                       | -                     | required  |

# Voorgestelde veranderingen
Om de applicatie nog te laten werken zal er data uit het ZRC, DRC en ZTC gehaald moeten worden.
Hieronder komt een eerste opzet over waar en hoe we dit zouden kunnen doen.

## Wijzigingen in SIA
Als eerste zullen er wijzigingen in SIA moeten plaats vinden op het model.
We moeten weten welke zaak gekoppeld is aan het signaal. Hiervoor zullen er extra velden nodig zijn op het datamodel.
Zonder deze wijziging zullen wij niet in staat zijn de benodigde gegevens op te kunnen halen om de backoffice nog te laten werken via de frontend.

```python
from django.db import models


class Signal(models.Model):
    # All fields that are now available.
    zaak_uuid = models.UUIDField()

    @property
    def zaak_url(self):
        url = "" # Hierin zal zich de url bevinden naar de zaak.
        return url.format(self.zaak_uuid)
```

Door deze 2 velden toe te voegen kan er op een makkelijke manier gekoppeld worden met

## Status lijst
Om te kunnen bepalen welke statussen mogelijk zijn moet er in het ZTC een lijst met statussen opgehaald kunnen worden.
Hiervoor moeten er een aantal settings worden toegevoegd.

```python
ZTC_CATALOGUS_UUID = '' # Deze waarde kan niet opgevraagd worden uit de api.
ZTC_ZAAKTYPE_UUID = '' # Deze waarde kan niet opgevraagd worden uit de api.
```

Met deze settings is het mogelijk om in het ZTC [statustype_list](https://ref.tst.vng.cloud/ztc/api/v1/schema/#operation/statustype_list) aan te roepen. Deze zal een overview van alle statussen terug geven die we nodig zullen hebben.

## Ophalen van de Zaak gegevens
Doordat we het zaak_uuid hebben opgeslagen, is het makkelijk om daaruit de zaak_url te herleiden. Hierdoor is het mogelijk om snel en makkelijk

## Updaten van de Zaak gegevens
Het updaten van een zaak kan het beste gebeuren via de patch zaak_partial_update. Met de patch zaak_partial_update kan je delen van de zaak updaten. Hierbij hoef je dan dus niet alles opnieuw op te halen en op te slaan.

## Ophalen van de Document gegevens
Om de documenten op te halen moet er gebruik worden gemaakt van de objectinformatieobject_list.
Hier is het mogelijk om een filter toe te passen door gebruik van een query parameter, object, die verwijst naar een zaak.

Hierna zal er mogelijk ook een request moeten komen om de data van het enkelvoudiginformatieobject op te vragen

# Authenticatie op de ZRC, DRC en ZTC endpoints
Momenteel mist de authenticatie nog. We willen hier gaan pushen op de manier die nu al bij Amsterdam in productie staat.
Dit is oauth met gebruik van JWT.
