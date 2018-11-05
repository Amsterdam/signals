# Aanpak
Hieronder wordt de aanpak beschreven. Het wordt opgedeeld in iteraties. Hierdoor wordt het
overzichtelijker in wat er zou moeten gebeuren. Ook door de opleveringen wat kleiner te maken is
ervoor gekozen om als eerste een synchronisatie stap te bouwen en dit daarna uit te breiden tot een
complete koppeling.

## Doel.
Het doel van dit project is het omzetten van de kern van het signalen systeem naar het ZRC en het
DRC waarbij ook gebruik wordt gemaakt van het ZTC voor het bijhouden van de mogelijke statussen.
Deze 3 componenten worden samengevoegd onder het ZDS, om zo te voorkomen dat alle componenten los
genoemd moeten worden bij elke benadering.

Dit dient ook om aan te kunnen tonen dat de nieuwe standaard (ZDS 2.0) werkt zoals verwacht.

### ZDS client
Er zal gebruik worden gemaakt van de ZDS Client. Dit is een client die het communiceren tussen
SIA en de ZDS components makkelijker moet maken. Deze client is echter nog niet compleet. Het kan
Voorkomen dat hier aanpassingen in gemaakt moeten worden. Ook kunnen we deze client uitbreiden om
makkelijker data te kunnen verwerken. Zoals 1 ZDS Client call maken om een document aan te maken
en te koppelen aan een zaak. Wat nu 3 losse calls zou worden.

## Iteratie #1
Voor iteratie 1 wordt ZDS gezien als een externe koppeling.

Dit heeft als voordeel dat de create endpoints volledig in gebruik genomen zullen worden. Zonder
dat er grote wijzigingen in het bestaande SIA platform nodig zijn. Er zal hier vooral in een losse
app gewerkt worden, ZDS. Deze zal vervolgens alles bevatten om de benodigde calls te kunnen maken.
Los van deze app mag niets gebruik maken van de ZDS Client.

### Opzetten staging env bij Amsterdam.
Dit heeft de hoogste prioriteit. Dit zorgt voor een goede en makkelijke manier om te beginnen met
developen.

**Hier worden de volgende onderdelen aangesproken**:
- ZRC [zaak_create](https://ref.tst.vng.cloud/zrc/api/v1/schema/#operation/zaak_create)
  - Zaak aanmaken. Dit zal de basis worden voor een signaal.
- ZRC [zaakobject_create](https://ref.tst.vng.cloud/zrc/api/v1/schema/#operation/zaakobject_create)
  - Dit is een koppeling tussen een zaak en een signaal. Hierdoor kan er vanuit de zaak worden
    doorverwezen naar een signaal voor meer informatie over een zaak.
- ZRC [status_create](https://ref.tst.vng.cloud/zrc/api/v1/schema/#operation/status_create)
  - Creëer een status voor een zaak. Dit wordt gebruikt bij het aanmaken van een signaal en bij het
    updaten van een status voor een signaal.
- DRC [enkelvoudiginformatieobject_create](https://ref.tst.vng.cloud/drc/api/v1/schema/#operation/enkelvoudiginformatieobject_create)
  - Dit is de foto die mee geüpload kan worden bij het aanmaken van een signaal.
- DRC [objectinformatieobject_create](https://ref.tst.vng.cloud/drc/api/v1/schema/#operation/objectinformatieobject_create)
  - Dit is de koppeling tussen de foto en de zaak. Gezien vanuit de foto

### Openstaande vraagstukken
- Hoe slaan we nu de statussen op die in het ZRC terecht moeten komen?
  - Een mogelijkheid is door dit op te slaan bij de huidige status choices.


## Iteratie #2
Voor iteratie 2 wordt ZDS als *single source of truth* gezien.

De data wordt hier niet langer vanuit SIA aangeleverd maar vanuit het ZDS. Dit betekend ook dat er
velden uit SIA kunnen verdwijnen. Dit is echter niet meteen nodig.

Dit is een belangrijk
onderdeel in de doelen van VNG. Door deze wijziging kunnen er ook al velden uit de SIA app
verwijderd kunnen worden.

**Hier worden de volgende onderdelen aangesproken**:
- Create api endpoints (zie Iteratie #1)
- ZRC [zaak_read](https://ref.tst.vng.cloud/zrc/api/v1/schema/#operation/zaak_read)
  - Het uitlezen van de zaak. Dit gebeurd via de zaak_url die opgeslagen op een signaal
- ZRC [zaakinformatieobject_list](https://ref.tst.vng.cloud/zrc/api/v1/schema/#operation/zaakinformatieobject_list)
  - Lees uit welke foto's verbonden zijn met de zaak.
- ZRC [status_list](https://ref.tst.vng.cloud/zrc/api/v1/schema/#operation/status_list)
  - Lees alle statussen uit die verbonden zijn met de zaak.

### Openstaande vraagstukken
- Worden er nu ook al model fields verwijderd uit SIA?

### Complicaties
- ?


## Iteratie #3
Voor iteratie 3 wordt het ZTC gebruikt voor de statussen.

Als de statussen ook uit het ZTC wordt gehaald wordt bijna alles overzet naar het ZDS.

In deze iteratie worden ook de overbodige model fields uit SIA gehaald. Dit zal alle vormen van
dubbele data moeten voorkomen.

Hier worden de volgende onderdelen aangesproken:
- Create api endpoints (zie Iteratie #1)
- Read ZRC (zie Iteratie #2)
- ZTC [statustype_list](https://ref.tst.vng.cloud/ztc/api/v1/schema/#operation/statustype_list)
  - Lees alle statussen die er voor een zaaktype zijn. (openbare melding, verhuizing, etc)

### Complicaties
- Hoe enforcen we de workflow op de statussen vanuit het ZTC?


## Iteratie #4
Hierin wordt er gekeken naar het overgebleven datamodel van SIA. Hieruit wordt een opzet gemaakt
voor een standaardisering van een MOR applicatie. Dit zal gebeuren op een algemeen niveau Zonder
op specifieke code in te gaan.

Ook zal hier worden gekeken naar het koppelen van NLX.

Dit laatste onderdeel is een wens van VNG. Deze heeft aan de hand van de ontwikkelingen het minste
prioriteit
