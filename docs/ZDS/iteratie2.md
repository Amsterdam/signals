# Read zaak

Vanaf dit punt gaat de data uit het zds gebruikt worden. Hiermee wordt de eerste stap tot complete
integratie gezet.

```python
from signals.apps.zds import zds_client


zds_client.zrc.retrive('zaak', zaak_url)
```

Returned fields:

| Naam                          | Type                                                                                  | Uitleg                                                                                                                                                |
|-------------------------------|---------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| url                           | string <uri> (Url)                                                                    |                                                                                                                                                       |
| identificatie                 | string (Identificatie)                                                                | De unieke identificatie van de ZAAK binnen de organisatie die verantwoordelijk is voor de behandeling van de ZAAK.                                    |
| bronorganisatie               | string (Bronorganisatie)                                                              | Het RSIN van de Niet-natuurlijk persoon zijnde de organisatie die de zaak heeft gecreeerd.                                                            |
| omschrijving                  | string (Omschrijving)                                                                 | Een korte omschrijving van de zaak.                                                                                                                   |
| zaaktype                      | string <uri> (Zaaktype)                                                               | URL naar het zaaktype in de CATALOGUS waar deze voorkomt                                                                                              |
| registratiedatum              | string <date> (Registratiedatum)                                                      | De datum waarop de zaakbehandelende organisatie de ZAAK heeft geregistreerd. Indien deze niet opgegeven wordt, wordt de datum van vandaag gebruikt.   |
| verantwoordelijkeOrganisatie  | string <uri> (Verantwoordelijke organisatie)                                          | URL naar de Niet-natuurlijk persoon zijnde de organisatie die eindverantwoordelijk is voor de behandeling van de zaak.                                |
| startdatum                    | string <date> (Startdatum)                                                            | De datum waarop met de uitvoering van de zaak is gestart                                                                                              |
| einddatum                     | string <date> (Einddatum)                                                             | De datum waarop de uitvoering van de zaak afgerond is.                                                                                                |
| einddatumGepland              | string <date> (Einddatum gepland)                                                     | De datum waarop volgens de planning verwacht wordt dat de zaak afgerond wordt.                                                                        |
| uiterlijkeEinddatumAfdoening  | string <date> (Uiterlijke einddatum afdoening)                                        | De laatste datum waarop volgens wet- en regelgeving de zaak afgerond dient te zijn.                                                                   |
| toelichting                   | string (Toelichting)                                                                  | Een toelichting op de zaak.                                                                                                                           |
| zaakgeometrie                 | object or object or object or object or object or object or object (GeoJSONGeometry)  |                                                                                                                                                       |
| status                        | string <uri> (Status)                                                                 | Indien geen status bekend is, dan is de waarde 'null'                                                                                                 |
| kenmerken                     | Array of object                                                                       | Lijst van kenmerken                                                                                                                                   |


# List zaakinformatieobject

```python
from signals.apps.zds import zds_client


zds_client.zrc.list('zaakinformatieobject')
```

Returned fields:

| Naam             | Type                            | Uitleg                                                                                                    |
|------------------|---------------------------------|-----------------------------------------------------------------------------------------------------------|
| informatieobject | string <uri> (Informatieobject) | URL-referentie naar het informatieobject in het DRC, waar ook de relatieinformatie opgevraagd kan worden. |


# List status

Let op. Filtering toegevoegd in versie 0.6.0


```python
from signals.apps.zds import zds_client


zds_client.zrc.list('status')
```

Returned fields:

| Naam              | Type                                      | Uitleg                                                                                |
|-------------------|-------------------------------------------|---------------------------------------------------------------------------------------|
| url               | string <uri> (Url)                        |                                                                                       |
| zaak              | string <uri> (Zaak)                       |                                                                                       |
| statusType        | string <uri> (Status type)                |                                                                                       |
| datumStatusGezet  | string <date-time> (Datum status gezet)   | De datum waarop de ZAAK de status heeft verkregen.                                    |
| statustoelichting | string (Statustoelichting)                | Een, voor de initiator van de zaak relevante, toelichting op de status van een zaak.  |
