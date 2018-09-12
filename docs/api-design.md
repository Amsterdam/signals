# API ontwerp voor SIA (voorstel versie: 2018-09-10)

Context:
    Het doorvoeren van API versionering vereist een aanpassing van de URL
    namespace van SIA. Hieronder staat een gestroomlijnde REST API voor
    integratie met externe systemen. Een doel wat in dit ontwerp is nagestreeft
    is om minder interne details zichtbaar te maken voor externe partijen.

    Huidig ontwerp gebruikt engelse termen in de URL namespace, maar dat
    kunnen we ook omzetten naar Nederlandse terminologie (zoals aanbevolen
    in het DSO API document).

Problemen huidige API:
    - Geen afspraken over aanpassingen in de API.
    - Database IDs zijn exposed.
    - geauthenticeerde endpoints exposen veel extra velden die eigelijk voor
      intern gebruik zijn
    - API spiegelt database tabellen

## Voorstel:

Onze API draait op:
    - ACC: https://acc.api.data.amsterdam.nl/signals/
    - PROD: https://api.data.amsterdam.nl/signals/


### Publieke API (ongeauthenticeerd)

`identifier` == `uuid`
Geen database ID's exposen in API.
Mogelijk nieuwe identifiers -> https://github.com/skorokithakis/shortuuid \[Pak liever iets anders. Base57... kom op zeg. —PvB]

`/v1/public/`

`/v1/public/signals/`
- POST
    - kan een signal aanmaken, location, reporter, etc. moeten meegestuurd
      worden.
    - geen image upload
    - Suggestie: Doe iets POE-achtigs (Post Once Exactly). —PvB

`/v1/public/signals/<identifier>/`
- GET
    - kan de meest recente staat van een signaal opvragen (en bijbehorende
      meest recente status, locatie, etc.), met alle gevoelige informatie
      eruit gefilterd

`/v1/public/signals/<identifier>/image` \[geen trailing slash, of `/images/` als meerdere images mogelijk zijn. —PvB]
- POST
    - upload image, dit is de enige manier om een image aan een signaal toe te voegen
    - Ook hier: POE —PvB

`/v1/public/terms/categories/`
- GET
    - lijst van alle categorien (hoofd en sub)


### Privé API (geauthenticeerd)
`/v1/private/signals/`
- POST
    - kan een signal aanmaken, location, reporter, etc. moeten meegestuurd
      worden.
    - geen image upload
- GET
    - lijst weergave van alle signalen
        - incl. filters via querystring

`/v1/private/signals/<identifier>/`
- GET
    - het volledige signaal (inc. gevoelige info als plaats)

`/v1/private/signals/<identifier>/updates/`
- GET
    - lijst van updates voor een gegeven signaal (of het nu status, locatie,
      of categorie betreft) kan gebruikt worden in frontend

`/v1/private/signals/<identifier>/image` \[geen trailing slash, of `/images/` als meerdere images mogelijk zijn. —PvB]
- POST
    - upload image, dit is de enige manier om een image aan een signaal toe te voegen

`/v1/private/signals/<identifier>/status` \[geen trailing slash —PvB]
- PUT
    - update op status, dit is de enige manier om een status te wijzigen

`/v1/private/signals/<identifier>/category` \[geen trailing slash —PvB]
- PUT
    - update op categorie

`/v1/private/signals/<identifier>/location` \[geen trailing slash —PvB]
- PUT
    - update op locatie

`/v1/private/signals/<identifier>/priority` \[geen trailing slash —PvB]
- PUT
    - update op prioriteit


Andere opmerkingen:
- Ik zou de namespace niet opdelen in een `/private/` en `/public/` deel.
- Meer consistentie wat betreft trailing slashes. Ik zou ze allemaal weghalen. Dat maakt de implementatie ook eenvoudiger.
