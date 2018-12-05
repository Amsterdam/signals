# Eerste iteratie: koppeling SIA en ZDS
In de eerste fase van de SIA-ZDS integratie zal er alleen een koppeling tot stand
gebracht worden tussen de twee systemen. In deze fase is het SIA systeem leidend
en volgt het ZDS systeem. Aan SIA wordt een extra Django app toegevoegd die zich
bezig houdt met de communicatie met het ZDS systeem. Alle kennis over het ZDS zal
binnen SIA in de eerder genoemde Django app worden verpakt. Om de koppeling te
testen moet het ZDS op de Amsterdamse infrastructuur draaien. Het blijft mogelijk
om SIA te gebruiken zonder de ZDS koppeling.

Op te leveren:
* een werkende en beveiligde installatie van het ZDS systeem op de Amstedamse
  infrastructuur
* een Django app binnnen SIA die communiceert met het ZDS systeem

Buiten scope:
* elke afhankelijkheid van SIA op het ZDS


## Create Zaak -> create_case

```python
from signals.apps.zds import zds_client


zds_client.zrc.create('zaak', zaak_data)
```

Hieronder vind je wat er in de zaak_data meegegeven moet worden.

Verplichte velden:

| ZRC                           | SIA                   | Beperkingen           |
|-------------------------------|-----------------------|-----------------------|
| bronorganisatie               | (RSIN van amsterdam)  | [1..9] characters     |
| zaaktype                      | (link naar ZTC)       | [1..200] characters   |
| verantwoordelijkeOrganisatie  | (link NNP)*           | [1..200] characters   |
| startdatum                    | incident_date_start   | -                     |

* NNP is een Niet-natuurlijk persoon.

Optionele velden:

| ZRC                           | SIA                   | Beperkingen           |
|-------------------------------|-----------------------|-----------------------|
| identificatie                 | signal_id             | <= 40 characters      |
| omschrijving                  |                       | <= 80 characters      |
| registratiedatum              | created_at            | -                     |
| einddatum                     | incident_date_end     | -                     |
| einddatumGepland              | operational_date      | -                     |
| uiterlijkeEinddatumAfdoening  | expire_date           | -                     |
| toelichting                   | text                  | <= 1000 characters    |
| zaakgeometrie                 | coordinaten           | -                     |
| kenmerken                     |                       | -                     |

## Create zaakobject -> connect_signal_to_case

```python
from signals.apps.zds import zds_client


zds_client.zrc.create('zaakobject', zaakobject_data)
```

Hieronder vind je wat er in de zaakobject_data meegegeven moet worden.

Verplichte velden:

| ZRC                   | SIA                     | Beperkingen               |
|-----------------------|-------------------------|---------------------------|
| zaak                  | (link naar de zaak)     | -                         |
| object                | (link naar de signal)   | [ 1 .. 200 ] characters   |
| type                  | "MeldingOpenbareRuimte" | ENUM                      |

Optionele velden:

| ZRC                   | SIA                   | Beperkingen               |
|-----------------------|-----------------------|---------------------------|
| relatieomschrijving   |                       | <= 80 characters          |


## Create status -> add_status_to_case

```python
from signals.apps.zds import zds_client


zds_client.zrc.create('status', status_data)
```

Hieronder vind je wat er in de status_data meegegeven moet worden.

Verplichte velden:

| Statussen             | SIA                 | Beperkingen               |
|-----------------------|---------------------|---------------------------|
| zaak                  | (link naar de zaak) | -                         |
| statusType            | state               | [ 1 .. 200 ] characters   |
| datumStatusGezet      | created_at          | -                         |

Optionele velden:

| Statussen             | SIA                 | Beperkingen               |
|-----------------------|---------------------|---------------------------|
| statustoelichting     | text                | <= 1000 characters        |


## Create enkelvoudiginformatieobject -> create_document

```python
from signals.apps.zds import zds_client


zds_client.drc.create("enkelvoudiginformatieobject", enkelvoudiginformatieobject_data)
```

Hieronder vind je wat er in de enkelvoudiginformatieobject_data meegegeven moet worden.

Verplichte velden:

| DRC                         | SIA                   | Beperkingen           |
|-----------------------------|-----------------------|-----------------------|
| creatiedatum                |                       | -                     |
| titel                       | document_name         | [1..200] characters   |
| auteur                      | uploader?             | [1..200] characters   |
| taal                        | "dut"                 | ENUM                  |
| informatieobjecttype        | (link naar het ZTC)*  | [1..200] characters   |

* opslaan in de settings

Optionele velden:

| DRC                         | SIA                   | Beperkingen           |
|-----------------------------|-----------------------|-----------------------|
| identificatie               |                       | <= 40 characters      |
| bronorganisatie             |                       | <= 9 characters       |
| vertrouwelijkaanduiding     |                       | ENUM                  |
| formaat                     |                       | <= 255 characters     |
| inhoud                      |                       | -                     |
| link                        | image                 | <= 200 characters     |
| beschrijving                |                       | <= 1000 characters    |


## Create objectinformatieobject -> add_document_to_case

```python
from signals.apps.zds import zds_client


zds_client.drc.create("objectinformatieobject", objectinformatieobject_data)
```

Hieronder vind je wat er in de objectinformatieobject_data meegegeven moet worden.

Verplichte velden:

| DRC                    | SIA                              | Beperkingen           |
|------------------------|----------------------------------|-----------------------|
| informatieobject       | (link naar het informatieobject) | -                     |
| object                 | (link naar de zaak)              | [1..200] characters   |
| objectType             | "zaak"                           | ENUM                  |
| registratiedatum       | timezone.now                     | -                     |

Optionele velden:

| DRC                    | SIA                   | Beperkingen           |
|------------------------|-----------------------|-----------------------|
| titel                  |                       | <= 200 characters     |
| beschrijving           |                       | <= 1000 characters    |

Het eventueel uitbreiden van de data die opgeslagen wordt is altijd nog mogelijk.
