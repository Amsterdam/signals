# Signalen Informatie Voorziening API V1
**Ter goedkeuring / commentaar is welkom**

De Signalen Informatie Voorziening (SIA) is na een kort ontwikkel proces live
gegaan in de zomer van 2018. De SIA applicatie bestaat uit twee delen, een 
frontend applicatie die door burgers en afhandelaars gebruikt wordt, en een
backend applicatie die de data en workflows in SIA beheert.

Dit document beschrijft alleen een deel van de backend applicatie, namelijk de
zogenaamde Application Programming Interface (API) die SIA aanbiedt. De API
vormt een technisch koppelvlak tussen de SIA backend en externe systemen en SIA
frontend. Bij de specificatie van een API zijn de afspraken over verdere
ontwikkeling van die API belangrijk en daarvoor is API versionering een
vereiste. In de sectie "Het voorgestelde API ontwerp" hieronder staat een
gestroomlijnde API voor integratie met externe systemen. Een doel wat in dit
ontwerp is nagestreeft is om minder interne details zichtbaar te maken voor
externe partijen.


## Uitgangspunten
### Semantic Versioning in de SIA backend
De [Semantic versioning][semver] standaard beschrijft de betekenis van een
versie nummers. SIA volgt deze standaard voor de APIs en voor de gehele backend
applicatie.

De huidige versie van de SIA backend applicatie heeft 3 versie nummers:

1. De gehele applicatie (omvattend de oude API, de nieuwe API en data handling)
   krijgt een versie nummer. Deze zijn gedocumenteerd op de Github [releases
   pagina][signals-releases] van het `signals` project op Github. In de
   communicatie vaak afgekort als bijvoorbeeld BE 0.6.2 (backend release 0.6.2).
2. De originele API heeft een versie nummer dat niet gecommuniceerd wordt via de
   API, maar intern wel wordt bijgehouden. Deze zijn als volgt: 0.x.y
3. De versie nummers en status van de V1 API zijn beschikbaar via de publieke
   API op https://api.data.amsterdam.nl/signals/releases en zijn als volgt:
   1.x.y

Notabene: als het PATCH getal in een versie nummer 0 is wordt het weggelaten,
versie nummer 1.1 is bijvoorbeeld de afkorting van 1.1.0.


### Versioning in de REST interface van SIA
SIA biedt een API aan volgens de REspresentational State Transfer (REST)
techniek, daarin wijkt SIA niet af van andere door Datapunt Amsterdam
ontwikkelde services. In REST APIs is het gebruikelijk het MAJOR versie nummer
van de API in de paden van de API zichtbaar te maken, bijvoorbeeld:
`/signals/v1/private/signals`.


## Het voorgestelde API ontwerp
### Publiek en ongeauthenticeerd
Burgers kunnen anoniem een melding doen, dit gebeurt via de publieke en
ongeauthenticeerde API --- ook als de melding gedaan wordt via [meldingen]. Dit
deel van de SIA API biedt een mogelijkheid om een melding aan te maken, er een
foto bij te voegen en de status van de melding te volgen. De publieke en
ongeauthenticeerde API biedt niet de mogelijkheid alle data bij een melding op
te vragen.

*Wat volgt veronderstelt kennis van REST APIs:*

`/signals/`
    - GET: Lijst van links naar de API versies.
`/signals/v1/`
    - GET: Lijst van links API pagina's binnen V1 API (publiek en niet publiek).
`/signals/v1/public/signals/`
    - GET: Wordt niet ondersteund.
    - POST: Aanmaken nieuwe melding (anoniem).
`/signals/v1/public/signals/<signal public id>`
    - GET: Melding gegevens (alleen de publieke) met een samenvatting van de
      updates daarop.
`/signals/v1/public/signals/<signal public id>/image`
    - GET: Opvragen foto bij een melding (als deze er is).
    - POST: Aanmaken foto bij melding.

`/signals/v1/public/terms/categories/`
    - GET: Lijst van hoofd categorieën met de onderliggende sub categorieën.
`/signals/v1/public/terms/categories/<main category slug>`
    - GET: Detail pagina voor hoofdcategorie bestaande uit een lijst van sub
      categorieën bij die hoofd categorie.
`/signals/v1/public/terms/categories/<main category slug>/sub_categories/<sub category slug>`
    - GET: Detail pagina voor een sub categorie.

`https://api.data.amsterdam.nl/signals/redoc/`
    - GET: Gegenereerde API documentatie in Swagger formaat.

### Publiek en Geauthenticeerd
De publiek en geauthenticeerde API is bedoelt voor koppelingen met externe 
partijen, handelingen binnen SIA die speciale rechten vereisen en toegang tot
gevoelige data. De [meldingen] backoffice applicatie gebruikt deze API aangezien
behandelaars potentieel gevoelige data en speciale rechten nodig hebben om hun
werk te doen. Verder houdt de backoffice applicatie een logboek bij voor iedere
melding. In dat logboek is te vinden wie wat heeft gedaan en wanneer.

`/signals/v1/private/signals/`
    - GET: Lijst meldingen.
    - POST: Aanmaken nieuwe melding (met bekende user).
`/signals/v1/private/signals/<signal id>`
    - GET: De melding en alle informatie die erbij hoort.
    - PUT / PATCH: Update op de melding. Accepteert ook veranderingen in status,
      categorie, locatie, prioriteit en notitie.
`/signals/v1/private/signals/<signal id>/history`
    - GET: Volle geschiedenis van de melding.
`/signals/v1/private/signals/<signal id>/image`
    - GET: Opvragen foto bij een melding (als deze er is).
    - POST: Aanmaken foto bij melding, geen updates.


## Mogelijke analysten API
Een derde groep gebruikers van SIA zijn analysten en diegenen die aan rapportages
over de afhandeling van meldingen werken. Deze groep gebruikt nu dezelfde API
endpoints als de frontend en zij hebben dezelfde toegang tot het systeem terwijl
ze niet de zelfde behoeften hebben. De SIA backend zou een aantal speciale,
alleen lezen, endpoints kunnen aanbieden die toegespitst zijn op de behoeftes
van analysten. Aangezien de SIA backend applicatie de meldingen data beheert en
toegang heeft tot de achterliggende database kunnen eventueel speciale queries
geschreven worden die de data samenvatten (of filteren). De resultaten van zo'n
query kunnen dan via de REST API worden aangeboden.


[meldingen]: https://meldingen.amsterdam.nl
[semver]: https://semver.org/
[signals-releases]: https://github.com/Amsterdam/signals/releases