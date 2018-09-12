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

#### Identifier

- `identifier` == `uuid`
- Geen database ID's exposen in API
- Mogelijk nieuwe identifiers -> https://github.com/skorokithakis/shortuuid 
    - [Pak liever iets anders. Base57... kom op zeg. —PvB]
        - max_lenght=22
            - Is mooier dan uuid?? korte urls?
? Waar moeten onze identifier aan voldoen?
    - Moet deze human-readable zijn? 
        - "Door te geven zijn via de telefoon..."   
        - e.g. "48510SXQ" (5 cijfers, 3 letters) ... ?
            - afstemmen met business (PO)
    - Moet niet te raden zijn
    - Moet niet oplopend zijn


#### Endpoints

`/`
- GET 
    - lijst beschikbare versies
        - `expiration_date` (initieel None) 
        - `status` (stable, beta, etc.)

`/v1/`
- GET
    - lijst beschikbare endpoints
    ? Hoeveel niveau's diep? (alleen /public /private tonen)
    ? HAL structuur of DRF router structuur 

`/v1/public/`
- GET
    - lijst beschikbare endpoints

`/v1/public/signals/`
- POST
    - kan een signal aanmaken, location, reporter, etc. moeten meegestuurd
      worden.
    - geen image upload (images/files kunnen niet verstuurd worden via JSON)
        - Daarom apart endpoint voor image upload

`/v1/public/signals/<identifier>`
- GET
    - Geeft de status van het signal terug. Verder geen gevoelig data
        - Dit is dus een hele minimale representatie van het object 
        - Op dit moment wordt dit gebruikt door Verbeter de buurt
            - Moet dit niet naar de `private` endpoints..?
    - "De API is niet orthogonaal. GET signals/id levert het signal inclusief image terwijl de POST in twee stappen verloopt. Als je het mooier wilt maken zou ik willen voorstellen GET signals/id/image toevoegen. (~estetisch)"

`/v1/public/signals/<identifier>/image`
- POST
    - upload image, dit is de enige manier om een image aan een signaal toe te voegen

`/v1/public/terms/categories/`
- GET
    - lijst van alle categorien (hoofd en sub)


### Privé API (geauthenticeerd)
`/v1/private/signals/`
- GET
    - lijst weergave van alle signalen
        - incl. filters via querystring
- POST
    - kan een signal aanmaken, location, reporter, etc. moeten meegestuurd worden.
    - geen image upload (images/files kunnen niet verstuurd worden via JSON)
        - Daarom apart endpoint voor image upload
    - kan meer dan het `public` POST endpoint, want je bent ingelogd
        - e.g. `priority`, `source` zetten

`/v1/private/signals/<identifier>`
- GET
    - het volledige signaal (inc. gevoelige info als plaats)
    - HAL urls naar sub resources
        ? Hoe moet dit precies? 
        - Ook als sub resources alleen maar PUT ondersteunen?
        - https://stackoverflow.com/questions/47941703/how-to-handle-nested-resources-with-json-hal
- PUT
    - partial update voor `status`, `category`, `location`, `priority`
        - Dus geen updates op directe `Signal` velden

`/v1/private/signals/<identifier>/image`
- POST
    - upload image, dit is de enige manier om een image aan een signaal toe te voegen

`/v1/private/signals/<identifier>/updates/`
- GET
    - lijst van updates voor een gegeven signaal (of het nu status, locatie,
      of categorie betreft) kan gebruikt worden in frontend


## Vraag / opmerkingen:

- Ik zou de namespace niet opdelen in een `/private/` en `/public/` deel.
    - Ok, wat zou het dan moeten worden? Willen we wel een duidelijk splitsing tussen auth en unauth endpoints?
    - We (wij als Datapunt) willen geen endpoints die verschillend gedrag vertonen bij wel of niet ingelogd zijn??  
- Na denken over: Doe iets POE-achtigs (Post Once Exactly). —PvB
    - Lijkt nog geen standaard voor te zijn?
        - ID's vanuit de client meesturen? Vraagt ook om FE aanpassingen
