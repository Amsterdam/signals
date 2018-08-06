"""
XML message templates, based on examples provided by Sigmax/Maarten Sukel.
"""

CREER_ZAAK = """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
       <soap:Body>
          <ZKN:zakLk01 xmlns:ZKN="http://www.egem.nl/StUF/sector/zkn/0310" xmlns:BG="http://www.egem.nl/StUF/sector/bg/0310" xmlns:mime="http://schemas.xmlsoap.org/wsdl/mime/" xmlns:gml="http://www.opengis.net/gml" xmlns:bag="http://www.vrom.nl/bag/0120" xmlns:soap12="http://schemas.xmlsoap.org/wsdl/soap12/" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/" xmlns:StUF="http://www.egem.nl/StUF/StUF0301" xmlns:tns="http://www.circlesoftware.nl/verseon/mng/webservice/2012" xmlns:tm="http://microsoft.com/wsdl/mime/textMatching/" xmlns:http="http://schemas.xmlsoap.org/wsdl/http/" xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns:xlink="http://www.w3.org/1999/xlink">
             <ZKN:stuurgegevens>
                <StUF:berichtcode>Lk01</StUF:berichtcode>
                <StUF:zender>
                   <StUF:organisatie>AMS</StUF:organisatie>
                   <StUF:applicatie>VER</StUF:applicatie>
                </StUF:zender>
                <StUF:ontvanger>
                   <StUF:organisatie>SMX</StUF:organisatie>
                   <StUF:applicatie>CTC</StUF:applicatie>
                </StUF:ontvanger>
                <StUF:referentienummer>{PRIMARY_KEY}</StUF:referentienummer>
                <StUF:tijdstipBericht>{TIJDSTIPBERICHT}</StUF:tijdstipBericht>
                <StUF:entiteittype>ZAK</StUF:entiteittype>
             </ZKN:stuurgegevens>
             <ZKN:parameters>
                <StUF:mutatiesoort>T</StUF:mutatiesoort>
                <StUF:indicatorOvername>V</StUF:indicatorOvername>
             </ZKN:parameters>
             <ZKN:object StUF:entiteittype="ZAK" StUF:sleutelGegevensbeheer="" StUF:verwerkingssoort="T">
                <ZKN:identificatie>{PRIMARY_KEY}</ZKN:identificatie>
                <ZKN:omschrijving>{OMSCHRIJVING}</ZKN:omschrijving>
                <ZKN:startdatum>{STARTDATUM}</ZKN:startdatum>
                <ZKN:registratiedatum>{REGISTRATIEDATUM}</ZKN:registratiedatum>
                <ZKN:einddatumGepland>{EINDDATUMGEPLAND}</ZKN:einddatumGepland>
                <ZKN:archiefnominatie>N</ZKN:archiefnominatie>
                <ZKN:zaakniveau>1</ZKN:zaakniveau>
                <ZKN:deelzakenIndicatie>N</ZKN:deelzakenIndicatie>
                <StUF:extraElementen>
                   <StUF:extraElement naam="Ycoordinaat">{Y}</StUF:extraElement>
                   <StUF:extraElement naam="Xcoordinaat">{X}</StUF:extraElement>
                </StUF:extraElementen>
                <ZKN:isVan StUF:entiteittype="ZAKZKT" StUF:verwerkingssoort="T">
                   <ZKN:gerelateerde StUF:entiteittype="ZKT" StUF:sleutelOntvangend="1" StUF:verwerkingssoort="T">
                      <ZKN:omschrijving>Uitvoeren controle</ZKN:omschrijving>
                      <ZKN:code>2</ZKN:code>
                   </ZKN:gerelateerde>
                </ZKN:isVan>
                <ZKN:heeftBetrekkingOp StUF:entiteittype="ZAKOBJ" StUF:verwerkingssoort="T">
                   <ZKN:gerelateerde>
                      <ZKN:adres StUF:entiteittype="AOA" StUF:verwerkingssoort="T">
                         <BG:wpl.woonplaatsNaam>Amsterdam</BG:wpl.woonplaatsNaam>
                         <BG:gor.openbareRuimteNaam>{OPENBARERUIMTENAAM}</BG:gor.openbareRuimteNaam>
                         <BG:huisnummer>{HUISNUMMER}</BG:huisnummer>
                         <BG:huisletter StUF:noValue="geenWaarde" xsi:nil="true"/>
                         <BG:postcode>{POSTCODE}</BG:postcode>
                      </ZKN:adres>
                   </ZKN:gerelateerde>
                </ZKN:heeftBetrekkingOp>
             </ZKN:object>
          </ZKN:zakLk01>
       </soap:Body>
    </soap:Envelope>"""

VOEG_ZAAK_DOCUMENT_TOE = """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
   <soap:Body>
      <ZKN:edcLk01 xmlns:ZKN="http://www.egem.nl/StUF/sector/zkn/0310" xmlns:StUF="http://www.egem.nl/StUF/StUF0301" xmlns:gml="http://www.opengis.net/gml" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:mime="http://www.w3.org/2005/05/xmlmime">
         <ZKN:stuurgegevens>
            <StUF:berichtcode>Lk01</StUF:berichtcode>
            <StUF:zender>
               <StUF:organisatie>AMS</StUF:organisatie>
               <StUF:applicatie>VER</StUF:applicatie>
            </StUF:zender>
            <StUF:ontvanger>
               <StUF:organisatie>SMX</StUF:organisatie>
               <StUF:applicatie>CTC</StUF:applicatie>
            </StUF:ontvanger>
            <StUF:referentienummer>1234567890</StUF:referentienummer>
            <StUF:tijdstipBericht>20180517132910</StUF:tijdstipBericht>
            <StUF:entiteittype>EDC</StUF:entiteittype>
         </ZKN:stuurgegevens>
         <ZKN:parameters>
            <StUF:mutatiesoort>T</StUF:mutatiesoort>
            <StUF:indicatorOvername>V</StUF:indicatorOvername>
         </ZKN:parameters>
         <ZKN:object StUF:entiteittype="EDC" StUF:sleutelVerzendend="2356402" StUF:sleutelOntvangend="" StUF:sleutelGegevensbeheer="2356402" StUF:verwerkingssoort="T">
            <ZKN:identificatie>{DOC_UUID}</ZKN:identificatie>
            <ZKN:dct.omschrijving>Foto</ZKN:dct.omschrijving>
            <ZKN:creatiedatum>20170520</ZKN:creatiedatum>
            <ZKN:ontvangstdatum StUF:noValue="geenWaarde" xsi:nil="true"/>
            <ZKN:titel>Onderwerp</ZKN:titel>
            <ZKN:beschrijving StUF:noValue="geenWaarde" xsi:nil="true"/>
            <ZKN:formaat>{DOC_TYPE}</ZKN:formaat>
            <ZKN:taal>NL</ZKN:taal>
            <ZKN:versie StUF:noValue="geenWaarde" xsi:nil="true"/>
            <ZKN:status>Definitief</ZKN:status>
            <ZKN:verzenddatum StUF:noValue="geenWaarde" xsi:nil="true"/>
            <ZKN:vertrouwelijkAanduiding>VERTROUWELIJK</ZKN:vertrouwelijkAanduiding>
            <ZKN:auteur>Tester</ZKN:auteur>
            <ZKN:inhoud mime:contentType="{DOC_TYPE_LOWER}" StUF:bestandsnaam="{FILE_NAME}">{DATA}</ZKN:inhoud>
            <ZKN:isRelevantVoor StUF:entiteittype="EDCZAK" StUF:verwerkingssoort="T">
               <ZKN:gerelateerde StUF:entiteittype="ZAK" StUF:sleutelVerzendend="2356401" StUF:sleutelOntvangend="" StUF:sleutelGegevensbeheer="2356401" StUF:verwerkingssoort="T">
                  <ZKN:identificatie>{ZKN_UUID}</ZKN:identificatie>
                  <ZKN:omschrijving>Onderwerp</ZKN:omschrijving>
                  <ZKN:isVan StUF:entiteittype="ZAKZKT" StUF:verwerkingssoort="T">
                     <ZKN:gerelateerde StUF:entiteittype="ZKT" StUF:verwerkingssoort="T">
                        <ZKN:omschrijving>Fietshandhaving Centrum</ZKN:omschrijving>
                        <ZKN:code>2</ZKN:code>
                        <ZKN:ingangsdatumObject StUF:noValue="geenWaarde" xsi:nil="true"/>
                     </ZKN:gerelateerde>
                  </ZKN:isVan>
               </ZKN:gerelateerde>
            </ZKN:isRelevantVoor>
         </ZKN:object>
      </ZKN:edcLk01>
   </soap:Body>
</soap:Envelope>"""


