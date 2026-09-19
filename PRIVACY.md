# Datenschutzerklärung

**EA FC 27 Markt-Bot von 21Drehen**

Stand: 19. September 2026

Diese Datenschutzerklärung informiert, welche personenbezogenen Daten die Discord-Anwendung **EA FC 27 Markt-Bot von 21Drehen** (der „Bot“) verarbeitet. Betreiber: **21Drehen**.

Sie gilt ergänzend zu den [Nutzungsbedingungen](TERMS.md) und zu den Datenschutzhinweisen von [Discord](https://discord.com/privacy).

---

## 1. Verantwortlicher

**21Drehen**  
Kontakt: [GitHub Issues — SryNotSry21/FUT](https://github.com/SryNotSry21/FUT/issues)

---

## 2. Welche Daten verarbeitet werden

Der Bot speichert nur, was für Slash-Befehle und Preis-Alerts nötig ist:

| Daten | Zweck |
|---|---|
| Discord-Nutzer-ID | Inhaber von `/watch` und `/beobachten`; Erwähnung (`@Nutzer`) beim Alert |
| Discord-Server-ID | Einstellungen und Alerts auf diesen Server begrenzen |
| Discord-Kanal-ID | Alert-Kanal aus `/setup` |
| Beobachtungs- und Watch-Einstellungen | EA-Karten-ID, Spielername, Plattform, %-Schwelle, optional Zielpreis („unter X Coins“), letzte bekannte Preise |
| Markt-Preis-Snapshots | Aktuelle FUT.GG-Preise mit dem letzten Scan vergleichen (ohne Nutzerbezug) |

Der Bot fordert **keinen** Message-Content-Intent an. Er speichert **keine** Discord-Nachrichtentexte, keine E-Mail-Adressen, keine IP-Adressen, keine Zahlungsdaten und **keine EA-Zugangsdaten**. Es gibt **keinen EA-Login**.

---

## 3. Zwecke und Rechtsgrundlagen

- Bereitstellung des Bots, den du einlädst oder per Slash-Befehl nutzt (Art. 6 Abs. 1 lit. b DSGVO — Vertrag / angeforderte Leistung).
- Zustellung von Alerts, Missbrauchsschutz, Stabilität (Art. 6 Abs. 1 lit. f DSGVO — berechtigtes Interesse).

Es findet **kein** Profiling zu Werbezwecken und **kein** Verkauf von Daten statt.

---

## 4. Empfänger und Drittland

- **Discord Inc.** übermittelt Slash-Befehle und Bot-Antworten (Discord-Infrastruktur, u. a. USA). Es gelten Discords Bedingungen und Standardvertragsklauseln, soweit Discord sie nutzt.
- **FUT.GG** (und deren CDN) erhalten nur Spielernamen oder Karten-IDs für Preisabfragen — **nicht** deine Discord-Nutzer-ID.
- Ein **Hoster** des Bots, falls die SQLite-Datei dort liegt.
- **Behörden**, wenn rechtlich vorgeschrieben.

---

## 5. Speicherdauer

- Watches und Beobachtungen bleiben, bis du sie mit `/unwatch` löschst, ein Admin sie entfernt oder der Bot vom Server genommen und die Daten vom Betreiber gelöscht werden.
- Preis-Snapshots werden durch spätere Scans überschrieben.
- Discord kann Interaktionsprotokolle nach eigenen Regeln speichern.

---

## 6. Deine Rechte

Soweit die DSGVO gilt, hast du das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung, Datenübertragbarkeit und Widerspruch (Art. 15–21 DSGVO) sowie das Recht, dich bei einer Aufsichtsbehörde zu beschweren.

Praktisch im Bot:

- `/unwatch` — eigene Alerts/Beobachtungen löschen
- `/watches` / `/beobachtungen` — gespeicherte Einträge ansehen
- Bot vom Server kicken — Verarbeitung auf diesem Server beenden
- GitHub-Issue — Löschung restlicher Einträge beim Betreiber verlangen

---

## 7. Minderjährige

Der Bot richtet sich an Personen, die Discord nutzen dürfen, nicht an Kinder unter 13 Jahren (oder dem höheren Mindestalter in deinem Land).

---

## 8. Änderungen

Diese Erklärung kann unter dieser URL aktualisiert werden. Das Datum oben wird dann angepasst.

---

## English summary

The unofficial Discord app **EA FC 27 Markt-Bot von 21Drehen** (operator: 21Drehen) stores Discord user/server/channel IDs and watch settings (including optional target prices) so alerts can be delivered. It does not read message content, does not collect EA logins, and does not sell data. Market lookups to FUT.GG use player names or card IDs only. You can delete watches with `/unwatch` or contact the operator via GitHub issues.
