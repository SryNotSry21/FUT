# Privacy Policy / Datenschutzerklärung

**EA FC 27 Markt-Bot von 21Drehen**

Last updated / Stand: 19 September 2026

This policy explains what the Discord application **EA FC 27 Markt-Bot von 21Drehen** (the “Bot”), operated by **21Drehen**, stores when you use it. It supplements the [Terms of Service](TERMS.md).

Diese Erklärung beschreibt, welche Daten die Discord-Anwendung **EA FC 27 Markt-Bot von 21Drehen** (der „Bot“), betrieben von **21Drehen**, bei der Nutzung speichert. Sie ergänzt die [Nutzungsbedingungen](TERMS.md).

---

## 1. Controller / Verantwortlicher

**21Drehen**  
Contact / Kontakt: [GitHub Issues](https://github.com/SryNotSry21/FUT/issues)

---

## 2. Data we store / Welche Daten gespeichert werden

The Bot only stores what is needed to run commands and alerts:

Der Bot speichert nur, was für Befehle und Alerts nötig ist:

| Data | Purpose |
|---|---|
| Discord user ID | Owner of a `/watch` alert; mention when it fires |
| Discord server (guild) ID | Scope watches and `/setup` to that server |
| Discord channel ID | Alert channel chosen with `/setup` |
| Player / card watch settings | EA card ID, name, platform, thresholds, last seen prices |
| Market price snapshots | Compare current prices with the previous scan (no Discord user attached) |

| Daten | Zweck |
|---|---|
| Discord-Nutzer-ID | Inhaber eines `/watch`-Alerts; Erwähnung beim Auslösen |
| Discord-Server-ID (Guild) | Watches und `/setup` auf diesen Server begrenzen |
| Discord-Kanal-ID | Alert-Kanal aus `/setup` |
| Watch-Einstellungen | EA-Karten-ID, Name, Plattform, Schwellen, letzte Preise |
| Markt-Preis-Snapshots | Aktuelle Preise mit dem letzten Scan vergleichen (ohne Nutzerbezug) |

The Bot does **not** request the Message Content Intent. It does **not** store Discord message text, e-mail addresses, IP addresses, payment data or **EA account credentials**. There is no EA login.

Der Bot fordert **keinen** Message-Content-Intent an. Er speichert **keine** Discord-Nachrichtentexte, E-Mail-Adressen, IP-Adressen, Zahlungsdaten oder **EA-Zugangsdaten**. Es gibt keinen EA-Login.

---

## 3. Legal basis / Rechtsgrundlage

Processing is required to provide the Bot you invited or used (contract / requested service) and to operate a stable, abuse-resistant app (legitimate interest).

Die Verarbeitung ist erforderlich, um den Bot bereitzustellen, den du eingeladen oder genutzt hast (Vertrag / angeforderte Leistung), und um den Dienst stabil und missbrauchsarm zu betreiben (berechtigtes Interesse).

---

## 4. Where data is processed / Wo Daten verarbeitet werden

Watch settings and snapshots are stored in a local SQLite database on the machine that runs the Bot. Discord delivers slash commands and receives the Bot’s replies through Discord’s infrastructure.

Watch-Einstellungen und Snapshots liegen in einer lokalen SQLite-Datenbank auf dem Rechner, der den Bot ausführt. Discord übermittelt Slash-Befehle und die Antworten des Bots über die Discord-Infrastruktur.

Player search and prices are requested from public market APIs (currently FUT.GG / their CDN). Those requests contain **player names or card IDs**, not your Discord user ID.

Spieler- und Preisanfragen gehen an öffentliche Markt-APIs (derzeit FUT.GG / deren CDN). Diese Anfragen enthalten **Spielernamen oder Karten-IDs**, nicht deine Discord-Nutzer-ID.

---

## 5. Retention / Speicherdauer

- Watches stay until you or a server admin remove them (`/unwatch`) or the Bot is removed from the server and data is deleted by the operator.
- Price snapshots are overwritten by later scans.
- Discord may retain message/command logs according to Discord’s own policy.

- Watches bleiben, bis du oder ein Admin sie entfernen (`/unwatch`) oder der Bot vom Server entfernt und die Daten vom Betreiber gelöscht werden.
- Preis-Snapshots werden durch spätere Scans überschrieben.
- Discord kann Nachrichten-/Command-Logs nach eigenen Regeln speichern.

---

## 6. Sharing / Weitergabe

We do not sell personal data. Data is only shared with:

Personenbezogene Daten werden nicht verkauft. Weitergabe nur an:

- **Discord**, as required to run a Discord app
- **Hosting** of the Bot, if a host processes the database
- **Authorities**, if legally required

- **Discord**, soweit für eine Discord-App nötig
- **Hosting** des Bots, falls ein Hoster die Datenbank verarbeitet
- **Behörden**, wenn rechtlich vorgeschrieben

---

## 7. Your rights / Deine Rechte

Depending on applicable law (including GDPR if it applies), you may request access, correction, deletion or restriction of stored data about you.

Je nach geltendem Recht (einschließlich DSGVO, soweit anwendbar) kannst du Auskunft, Berichtigung, Löschung oder Einschränkung der zu dir gespeicherten Daten verlangen.

Practical options:

Praktisch:

- `/unwatch` removes your watch for a card
- `/watches` shows watches stored for you on that server
- Kick or ban the Bot from a server to stop processing there
- Open a GitHub issue to ask the operator to delete remaining records

- `/unwatch` entfernt deinen Watch für eine Karte
- `/watches` zeigt deine gespeicherten Watches auf dem Server
- Kick/Ban des Bots beendet die Verarbeitung auf diesem Server
- GitHub-Issue, wenn der Betreiber restliche Einträge löschen soll

---

## 8. Children / Minderjährige

The Bot is meant for users who are allowed to use Discord. It is not directed at children under 13 (or the higher age required in your country).

Der Bot richtet sich an Personen, die Discord nutzen dürfen, nicht an Kinder unter 13 Jahren (oder dem höheren Alter in deinem Land).

---

## 9. Changes / Änderungen

This policy may be updated at this URL. The “last updated” date above will change when it does.

Diese Erklärung kann unter dieser URL aktualisiert werden. Das Datum oben wird dann angepasst.

---

## 10. Contact / Kontakt

[GitHub Issues — SryNotSry21/FUT](https://github.com/SryNotSry21/FUT/issues)
