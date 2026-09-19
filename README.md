# EA FC 27 Markt-Bot von 21Drehen

Offizielle Discord-Anwendung von **21Drehen**. Der Bot prüft den EA-FC-27-**PlayStation**-Markt (Preise über FUT.GG), vergleicht sie und schickt Alerts bei starken Bewegungen.

Du musst **keinen eigenen Bot erstellen**. Einfach den offiziellen Bot einladen und auf dem Server einrichten.

© 2026 21Drehen. Alle Rechte vorbehalten. Kopieren oder Nachbauen ist nicht erlaubt. Siehe [LICENSE](LICENSE) und [Nutzungsbedingungen](TERMS.md).

## Einladen

Du brauchst auf dem Server **Server verwalten**.

**[Bot einladen](https://discord.com/oauth2/authorize?client_id=1550876389849174016&scope=bot+applications.commands&permissions=2147600448)**

Rechte, die der Bot braucht: Nachrichten senden, Embeds, Slash-Befehle.

## Einrichten auf dem Server

1. Textkanal für Alerts anlegen, z. B. `#markt-alerts`.
2. Als Admin ausführen:

   `/setup kanal:#markt-alerts schwelle:10 auto_scan:True min_preis:10000`

3. Danach postet der Bot starke Marktbewegungen in diesen Kanal.
4. Optional eigene Karten:

   - `/watch spieler:Mbappé schwelle_prozent:8` — Alert bei %-Änderung
   - `/beobachten spieler:Mbappé unter:2000000` — Alert unter Zielpreis

Ausführlich in Discord: **`/einrichten`**. Alle Befehle: **`/hilfe`**. Datenschutz: **`/datenschutz`**.

## Befehle

| Command | Funktion |
|---|---|
| `/einrichten` | Setup-Erklärung für diesen Server |
| `/setup` | Alert-Kanal, Auto-Scan und Schwelle (Admin) |
| `/preis` | Aktuellen PlayStation-Preis |
| `/suche` | Spieler suchen |
| `/vergleichen` | Zwei Karten vergleichen (PS) |
| `/watch` | Alert bei %-Änderung |
| `/beobachten` | Alert unter Zielpreis |
| `/unwatch` | Alert entfernen |
| `/watches` | Alle manuellen Alerts |
| `/beobachtungen` | Nur Zielpreis-Beobachtungen |
| `/alert` | Alert jetzt senden |
| `/markt` | Momentum der letzten Stunden |
| `/schnapper` | Unter Ø-BIN oder am Tiefpreis (Vorjahr nur als Hinweis) |
| `/hilfe` | Kurzanleitung |
| `/datenschutz` | Datenschutzerklärung |

Der Bot loggt sich **nicht** in EA-Accounts ein und handelt nicht auf dem Transfermarkt.

## Rechtliches

- [Nutzungsbedingungen](TERMS.md)
- [Datenschutzerklärung](PRIVACY.md)
- [Lizenz — alle Rechte vorbehalten](LICENSE)
