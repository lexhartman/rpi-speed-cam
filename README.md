# Raspberry Pi 5 Snelheidscamera (Speed Cam Pi)

Dit project verandert je Raspberry Pi 5 met Camera Module 3 in een geavanceerde snelheidscamera. Het systeem detecteert voertuigen, berekent hun snelheid en slaat foto's op van overtredingen. Via een webinterface kun je live meekijken, instellingen wijzigen en de geschiedenis bekijken.

## Functionaliteiten

*   **Snelheidsmeting**: Nauwkeurige berekening op basis van twee virtuele lijnen.
*   **Webinterface**: Live beelden, configuratie en geschiedenis (beveiligd met inlog).
*   **Notificaties**: Ondersteuning voor Telegram, Pushover en Webhooks (bijv. voor WhatsApp via externe diensten).
*   **Opslagbeheer**: Automatische opschoning van oude beelden als de schijf vol raakt.
*   **Docker**: Eenvoudige installatie en updates.

## Benodigdheden

*   Raspberry Pi 5 (of 4, maar 5 aanbevolen voor betere prestaties).
*   Raspberry Pi Camera Module 3 (of compatibel).
*   Docker & Docker Compose.

## Installatie

1.  **Clone de repository:**
    ```bash
    git clone https://github.com/lexhartman/rpi-speed-cam.git    
    ```
    
    ```bash
    cd rpi-speed-cam
    ```
    

2.  **Installeer Docker (indien nog niet aanwezig):**
    ```bash
    curl -sSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    # Log uit en weer in om de groepswijziging te activeren
    ```

3.  **Start de applicatie:**
    ```bash
    docker-compose up -d
    ```

    *Let op: De eerste keer duurt het even om de container te bouwen.*

4.  **Open de webinterface:**
    Ga in je browser naar `http://<IP-van-je-Pi>:8000`.
    
    *   **Standaard Inlog:**
        *   Gebruikersnaam: `admin`
        *   Wachtwoord: `change_me` (Wijzig dit direct in `config/config.yaml` of via de interface!)

## Configuratie & Kalibratie

### 1. Kalibratie (Cruciaal!)
Voor een nauwkeurige snelheidsmeting moet het systeem de echte afstand weten tussen de twee virtuele lijnen op het beeld.

1.  Markeer twee lijnen op de weg (bijv. met krijt of tape) met een bekende tussenafstand (bijv. 5 meter).
2.  Ga in de webinterface naar het **Dashboard**.
3.  Klik op **"Edit Lines"**.
4.  Sleep de blauwe lijn (Start) en rode lijn (Eind) zodat ze overeenkomen met de markeringen op de weg.
5.  Ga naar **Settings** en vul bij "Real Distance" de afstand in meters in (bijv. `5.0`).
6.  Klik op **Save Configuration**.

### 2. Notificaties
Je kunt notificaties instellen in het tabblad **Settings**.
*   **Telegram**: Maak een bot aan via @BotFather en vul de Token en Chat ID in.
*   **Webhook**: Voor integraties met Home Assistant of andere systemen.

## Troubleshooting

*   **Camera niet gevonden:**
    Zorg dat de camera correct is aangesloten en werkt (`rpicam-hello` op de Pi).
    Als je Docker gebruikt, zorg dat de container toegang heeft tot `/dev/video0`.
    Op de Raspberry Pi 5 wordt `libcamera` gebruikt. De container gebruikt OpenCV, wat soms een compatibiliteitslaag nodig heeft. Als het beeld zwart blijft, probeer dan de camera instellingen in `config/config.yaml` aan te passen of gebruik `libcamerify` op de host als dat nodig is voor legacy apps.

*   **Snelheid wijkt af:**
    Controleer de "Real Distance" instelling. Een kleine afwijking in meters heeft grote invloed op de berekende snelheid. Zorg ook dat de lijnen haaks op de rijrichting staan voor het beste resultaat.

## Ontwikkeling

Wil je aanpassingen maken aan de code?
De broncode staat in de `src` map. Na aanpassingen moet je de container opnieuw bouwen:
```bash
docker-compose up -d --build
```
