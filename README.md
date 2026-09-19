# EA FC 27 Markt-Bot von 21Drehen

Discord-Bot, der den **EA FC 27 Ultimate Team**-Markt über öffentliche FUT.GG-API-Schnittstellen überwacht, Preise vergleicht und Alerts schickt, wenn sich eine Karte stark bewegt.

Du kannst den Scanner **marktweit automatisch** laufen lassen und denselben Alert **manuell auf einzelne Spieler** legen.

## Was der Bot kann

- Spieler über die FUT.GG-Suche finden (`/suche`, Autocomplete in den anderen Commands)
- Live-Preise für **PlayStation/Konsole** und **PC** aus den FUT.GG-Preisblobs lesen
- Zwei Karten vergleichen, inklusive PS-vs-PC-Spread
- Automatischer Markt-Scan: starke Pumps/Crashes ins Alert-Channel posten
- `/watch`: Alert fest auf eine bestimmte Karte legen (eigene %- oder Coin-Schwelle)
- `/alert`: denselben Alert sofort manuell auslösen, ohne auf die Schwelle zu warten

Datenquelle ist [FUT.GG](https://www.fut.gg) (Suche, Momentum, CDN-Preisblobs). FUTBIN-Suche ist als optionaler Fallback verdrahtet, wird aber von Cloudflare oft blockiert.

Der Bot loggt sich **nicht** in EA-Accounts ein und handelt nicht auf dem Transfermarkt.

## Discord-Befehle

| Command | Funktion |
|---|---|
| `/setup` | Alert-Kanal, Auto-Scan und Standard-Schwelle (Admin) |
| `/preis` | Aktuellen PS- und PC-Preis einer Karte |
| `/suche` | Spieler suchen |
| `/vergleichen` | Zwei Karten vergleichen |
| `/watch` | Manuellen Alert für eine Karte setzen |
| `/unwatch` | Manuellen Alert entfernen |
| `/watches` | Alle manuellen Alerts des Servers |
| `/alert` | Alert für eine Karte **jetzt** senden |
| `/markt` | Momentum der letzten Stunden |
| `/hilfe` | Kurzanleitung |

Typischer Ablauf:

1. Bot einladen, in einem Channel `/setup kanal:#markt-alerts schwelle:10 auto_scan:True` ausführen.
2. Danach scannt der Bot den Markt im Hintergrund und postet starke Bewegungen.
3. Zusätzlich `/watch spieler:Mbappé schwelle_prozent:8` für Karten, die dir persönlich wichtig sind.

## Setup

### 1. Discord-Application

1. Unter [Discord Developer Portal](https://discord.com/developers/applications) eine Application anlegen.
2. Bot-User erstellen, Token kopieren.
3. OAuth2-Invite mit den Scopes `bot` und `applications.commands`.
4. Rechte: Nachrichten senden, Embeds, Slash-Commands. Keine Message-Content-Intent nötig.
5. Unter **App information → Legal** diese öffentlichen URLs eintragen:

   - Terms of Service: `https://github.com/SryNotSry21/FUT/blob/main/TERMS.md`
   - Privacy Policy: `https://github.com/SryNotSry21/FUT/blob/main/PRIVACY.md`

### 2. Bot starten

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# DISCORD_TOKEN in .env eintragen
python -m futbot
```

Optional `DISCORD_GUILD_ID` setzen, damit Slash-Commands sofort auf deinem Server erscheinen (sonst globale Sync, bis zu einer Stunde).

### Docker

```bash
cp .env.example .env
docker compose up --build -d
```

## CLI ohne Discord

Nützlich zum Testen der Markt-APIs:

```bash
python -m futbot lookup "Mbappe"
python -m futbot compare "Mbappe" "Haaland"
python -m futbot movers --stunden 24
```

## Konfiguration

| Variable | Default | Bedeutung |
|---|---|---|
| `DISCORD_TOKEN` | — | Bot-Token |
| `DISCORD_GUILD_ID` | leer | Slash-Commands nur auf diesen Server syncen |
| `FUT_GAME_YEAR` | `27` | EA FC 27 |
| `POLL_INTERVAL_SECONDS` | `120` | Abstand zwischen Markt-Scans |
| `DEFAULT_THRESHOLD_PCT` | `10` | Default für Auto-Scan und `/watch` |
| `SCAN_MIN_PRICE` | `10000` | Fodder unter diesem Preis ignorieren |
| `ALERT_COOLDOWN_MINUTES` | `30` | Spam-Schutz pro Watch |
| `DATABASE_PATH` | `data/futbot.db` | SQLite-Datei für Watches und Snapshots |

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Die Live-Tests treffen die echten FUT.GG-Endpunkte und werden übersprungen, wenn das Netz sie blockt.

## Rechtliches

- [Nutzungsbedingungen / Terms of Service](TERMS.md)
- [Datenschutzerklärung / Privacy Policy](PRIVACY.md)

## APIs

- `GET https://www.fut.gg/api/fut/players/v2/27/?name=` — Spielersuche
- `GET https://www.fut.gg/api/fut/global-search/27/players/?q=` — Fallback-Suche
- `GET https://www.fut.gg/api/fut/players/v2/momentum/24/?game=27` — Momentum
- `GET https://s3.eu-west-2.amazonaws.com/game-assets.fut.gg/27/cdn-data/player-prices-index.json`
- `GET https://s3.eu-west-2.amazonaws.com/game-assets.fut.gg/27/cdn-data/player-prices-ps5-dyn.json`
- `GET https://s3.eu-west-2.amazonaws.com/game-assets.fut.gg/27/cdn-data/player-prices-pc-dyn.json`
