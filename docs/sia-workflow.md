# Documentatie workflow in Signalen Informatievoorziening Amsterdam (SIA)

De meldingen in de SIA doorlopen een proces van een aantal stappen. Deze
workflow wordt in SIA gemodelleerd als een, in technische termen,
"state machine". De status van een melding wordt gebruikt om bij te houden waar
in het proces een melding zich bevindt en welke vervolgstappen mogelijk zijn.


## Statussen in de SIA workflow
De statussen in de SIA workflow vallen uiteen in twee typen, statussen die door
de gebruiker uitgekozen kunnen worden en statussen die door het systeem zelf 
gebruikt worden. Een status van het tweede type noemen we in het vervolg een
*systeemstatus*.

* **LEEG**: Deze systeemstatus wordt gebruikt voor meldingen die via de publieke,
  niet geauthenticeerde, API binnenkomen.
* **GEMELD**: Status van de eerste stap in het behandel proces binnen SIA.
* **AFWACHTING**: (input nodig van functioneel beheer)
* **ON_HOLD**: (input nodig van functioneel beheer)
* **BEHANDELING**: Status voor meldingen die in behandeling zijn en waarvan dat
  proces vanuit de SIA back office applicatie wordt begeleid.
* **AFGEHANDELD**: Status voor meldingen die afgehandeld zijn in SIA.
* **GEANNULEERD**: Status voor meldingen die niet in behandeling genomen worden.


* **TE_VERZENDEN**: Systeemstatus voor meldingen die verzonden moeten worden
  naar een externe partij om daar afgehandeld te worden.
* **VERZONDEN**: Systeemstatus voor meldingen waarvan de verzending naar een 
  extern systeem succesvol is verlopen. Meldingen met deze status staan dus uit
  bij een externe partij.
* **VERZENDEN_MISLUKT**: Systeemstatus voor meldingen waarvan de verzending naar
  een extern systeem misluk is.
* **AFGEHANDELD_EXTERN**: Systeemstatus voor meldingen die bij een externe 
  partij uitstonden en zijn afgehandeld.


## Toegestane status overgangen binnen SIA workflow

* van **LEEG** naar **GEMELD**
* van **GEMELD** naar **GEMELD**, **AFWACHTING**, **BEHANDELING**, **ON_HOLD**,
  **AFGEHANDELD**, **GEANNULEERD** of **TE_VERZENDEN**
* van **AFWACHTING** naar **AFWACHTING**, **BEHANDELING**, **ON_HOLD**,
  **AFGEHANDELD**, **GEANNULEERD** of **TE_VERZENDEN**
* van **BEHANDELING** naar **AFWACHTING**, **BEHANDELING**, **ON_HOLD**,
  **AFGEHANDELD**, **GEANNULEERD** of **TE_VERZENDEN**
* van **ON_HOLD** naar **GEMELD**, **AFWACHTING**, **BEHANDELING**, **ON_HOLD**,
  **AFGEHANDELD**, **GEANNULEERD** of **TE_VERZENDEN**
* van **TE_VERZENDEN** naar **VERZONDEN**, **VERZENDEN_MISLUKT**
* van **VERZONDEN** naar **AFGEHANDELD_EXTERN**
* van **VERZENDEN_MISLUKT** naar **GEMELD** of **TE_VERZENDEN**
* van **AFGEHANDELD_EXTERN** naar **AFGEHANDELD** of **GEANNULEERD**


## Implementatie
De data structuur (een Python dictionary) met toegelaten status overgangen is te
vinden in het volgende bron bestand: `/api/app/signals/apps/signals/workflow.py`.
