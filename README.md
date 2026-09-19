# EA FC 27 Marktanalyse-Bot (FUT)

Discord-Bot für **EA Sports FC Ultimate Team**-Marktanalyse: Preise nachschlagen, Snipe-Kandidaten im Cache finden, Preisalarme und eine persönliche Watchlist.

v1 nutzt einen **FUTBIN-Adapter hinter einem Interface** (`PriceProvider`). Live-HTTP zu FUTBIN ist absichtlich **nicht** verdrahtet — der Adapter liefert ein Mock-/Beispieldataset, damit alle Slash-Commands ohne externe APIs laufen. Standardmarkt: **PlayStation** (Konsolen-/PS-Preise).

English: Discord.js v14+ TypeScript skeleton. Analysis only — no buying, bidding, or unofficial EA companion / UTAS automation.

---

## Features (v1)

| Command | Beschreibung |
| --- | --- |
| `/preis` | Aktuellen Marktpreis einer Karte (Standard: PlayStation) |
| `/snipe` | Unterbewertete Karten vs. Erwartungspreis im Stunden-Cache |
| `/alert set\|list\|remove` | Preisalarme (DM-Hook, wenn die Schwelle im Cache gekreuzt wird) |
| `/watchlist add\|list\|remove` | Persönliche Watchlist inkl. PS-Preis aus dem Cache |

Weitere Bausteine:

- `PriceProvider` mit `searchPlayers`, `getPrice`, `findUnderpriced`
- `FutbinAdapter` (Mock + TODOs für HTTP, Rate-Limits, ToS)
- In-Memory `PriceCache` (~1 Stunde TTL, Redis-Interface vorbereitet)
- In-Memory Alerts + Scheduler-Hook
- In-Memory Watchlist (pro Discord-User)

---

## Voraussetzungen

- Node.js 20+
- Eine [Discord Application](https://discord.com/developers/applications) mit Bot

## Discord-App einrichten

1. [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**.
2. Unter **Bot**: Bot anlegen, Token kopieren (`DISCORD_TOKEN`). Message-Content-Intent wird **nicht** benötigt (nur Slash-Commands).
3. Unter **OAuth2 → General**: **Application ID** kopieren (`DISCORD_CLIENT_ID`).
4. Unter **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot permissions: mindestens `Send Messages`, `Embed Links` (optional `Use Slash Commands` ist implizit über den Scope abgedeckt)
5. Invite-URL öffnen und den Bot auf deinen Test-Server einladen.
6. Developer Mode in Discord aktivieren → Rechtsklick auf den Server → **Copy Server ID** (`DISCORD_GUILD_ID`, nur für schnelle Guild-Commands in Dev).

## Installation & Start

```bash
git clone <repo>
cd <repo>
cp .env.example .env
# DISCORD_TOKEN und DISCORD_CLIENT_ID eintragen
# DISCORD_GUILD_ID für sofortige Command-Registrierung auf dem Test-Server

npm install
npm run register-commands
npm run dev
```

| Script | Zweck |
| --- | --- |
| `npm run dev` | Start mit `tsx watch` (Reload bei Änderungen) |
| `npm run build` | TypeScript → `dist/` |
| `npm start` | `node dist/index.js` (nach `build`) |
| `npm run register-commands` | Slash-Commands per REST registrieren |
| `npm test` | Smoke-Tests (Cache, Mock-Adapter, Stores, Embeds) |

Ohne `DISCORD_GUILD_ID` registriert `register-commands` **globale** Commands (Propagierung bis ca. 1 Stunde). Mit Guild-ID erscheinen `/preis`, `/snipe`, `/alert` und `/watchlist` sofort auf diesem Server.

---

## Architektur

```
Discord slash commands
        │
        ▼
  Command handlers  ── embeds (DE copy)
        │
        ▼
 CachedPriceProvider  ← PriceCache (~1h, Memory / Redis-ready)
        │
        ▼
   FutbinAdapter  implements PriceProvider
        │
        ├── mock catalog (v1, default)
        └── TODO: HTTP (ToS + rate limits first)

AlertStore + WatchlistStore (in-memory, per user)
        │
        ▼
 alert-checker scheduler (compares alerts vs cache, optional DM)
```

Nur **ein** Datenadapter hängt hinter dem Interface: FUTBIN. Ein späterer Provider (offizielle/lizenzierte Quelle) kann `PriceProvider` implementieren und in `createBotContext` getauscht werden.

### Cache

`PriceCache` spricht ein `CacheBackend` an. v1: `MemoryCacheBackend`. Später z. B. Redis mit derselben `get` / `set` / `delete`-Fläche — Command-Code bleibt unverändert.

### Alerts

Der Scheduler prüft periodisch (Standard: 15 min) Alerts gegen `provider.getPrice` (also gegen den Stunden-Cache, kein Extra-FUTBIN-Burst). Bei Treffer: DM-Versuch. Das ist ein Hook, keine persistente Queue.

In-Memory-Stores sind nach Prozess-Neustart leer. Für Produktion: Datenbank nachrüsten.

---

## Live-FUTBIN (noch nicht aktiv)

Der Adapter dokumentiert TODOs für HTTP. Bevor ihr Live-Requests einschaltet:

- FUTBIN **Terms of Service**, robots.txt und etwaige API-/Lizenzhinweise lesen
- Aggressiv cachen (dieser Bot hat bereits ~1h TTL)
- Rate-Limits einhalten (konservativ, `Retry-After` / 429 beachten)
- Kein paralleles Stampede beim Cache-Expiry
- HTML-Scraping nur als letzter Ausweg; JSON/öffentliche Endpunkte bevorzugen

**Dieser Bot kauft, bietet und listet nicht.** Keine inoffiziellen EA-Companion-/FUT-Web-App-/UTAS-Sessions, keine Automatisierung gegen EA-Server.

---

## Umgebungsvariablen

Siehe `.env.example`.

| Variable | Pflicht | Default |
| --- | --- | --- |
| `DISCORD_TOKEN` | ja | — |
| `DISCORD_CLIENT_ID` | ja | — |
| `DISCORD_GUILD_ID` | nein | globale Commands |
| `DEFAULT_PLATFORM` | nein | `ps` |
| `PRICE_CACHE_TTL_MS` | nein | `3600000` (1h) |
| `ALERT_CHECK_INTERVAL_MS` | nein | `900000` (15 min) |

---

## Projektstruktur

```
src/
  index.ts                  Bot-Entry (Gateway)
  register-commands.ts      REST-Command-Deploy
  commands/                 preis, snipe, alert, watchlist
  market/                   PriceProvider, FutbinAdapter, cache
  stores/                   alerts + watchlist
  scheduler/                alert-checker hook
  embeds/                   deutsche Embed-Texte
tests/smoke.test.ts
```

Mock-Katalog: `src/market/mock-data.ts` (Beispiele, keine Live-IDs).
