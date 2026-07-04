# KlikAanKlikUit voor Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integratie voor de KlikAanKlikUit / Trust ICS-2000 hub. Je bedient je lampen, dimmers, schakelaars en gongs vanuit HA, en leest de deurbel en sensoren uit voor automatiseringen. Instellen gaat volledig via de interface, geen YAML nodig.

## Wat je krijgt

- Al je KAKU-apparaten als los apparaat in Home Assistant, netjes onder de hub gegroepeerd.
- Lampen en schakelaars als `light`, dimmers met helderheidsregeling.
- Gongs als knop: indrukken laat de gong klinken, ook bruikbaar in automatiseringen.
- Deurbel en wandschakelaar als `binary_sensor`, zodat je er automatiseringen op kunt maken.
- Temperatuur en vochtigheid van je Zigbee-sensoren.
- Bediening lokaal via je netwerk waar het kan, met de cloud als terugval.

## Installeren

1. Open HACS, klik rechtsboven op de drie puntjes en kies **Aangepaste repositories**.
2. Vul de URL van deze repository in en kies type **Integratie**.
3. Zoek in HACS op **KlikAanKlikUit** en download de integratie.
4. Herstart Home Assistant.
5. Ga naar **Instellingen > Apparaten en diensten > Integratie toevoegen**, zoek **KlikAanKlikUit** en vul je MAC-adres, e-mailadres en wachtwoord in. Dit zijn dezelfde gegevens als in de KlikAanKlikUit- of Trust-app.

Je apparaten verschijnen daarna automatisch.

## Instellingen

Bij de integratie kun je onder **Opties** het volgende aanpassen zonder opnieuw te installeren:

- **Poll-interval:** hoe vaak de status uit de cloud wordt opgehaald, in seconden (minimaal 5). Lager betekent dat sensoren en de deurbel sneller reageren in automatiseringen, maar zorgt voor meer cloudverkeer.
- **Lokaal IP van de hub:** vul dit in als je zeker wilt weten dat commando's lokaal gaan. Handig als je hub op een ander netwerk of VLAN staat en automatisch zoeken niet lukt.
- **Aantal pogingen en pauze:** hoe vaak een commando herhaald wordt en met welke tussenpauze. Handig als een apparaat af en toe een signaal mist.

## Hoe lokaal en cloud samenwerken

Besturen gaat lokaal via je netwerk zodra HA de hub daar vindt, en valt anders automatisch terug op de cloud. Uitlezen van de status gaat altijd via de cloud, want de ICS-2000 kan de status niet lokaal teruggeven. Na een commando toont HA meteen de nieuwe stand, en de cloud bevestigt dat kort daarna. Wijzigingen die je in de KlikAanKlikUit-app maakt verschijnen ook in HA, bij de volgende poll.

Een klassieke afstandsbediening die rechtstreeks naar een ontvanger zendt, buiten de hub om, is niet zichtbaar in HA. Dat signaal bereikt de cloud niet.
