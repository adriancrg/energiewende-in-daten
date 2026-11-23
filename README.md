# Energiewende in Daten – Analyse des deutschen Strommarkts

> **Status:** in Arbeit. Analyse und Ergebnisse kommen Schritt für Schritt dazu.

## Ziel

In diesem Projekt analysiere ich den deutschen Strommarkt seit 2020 mit stündlichen Daten.
Ich möchte verstehen, wie man die Energiewende in den Daten sieht: Wann gibt es viel Strom
aus Sonne und Wind? Wann sind die Strompreise negativ? Und wie gut kann man den
Stromverbrauch für den nächsten Tag vorhersagen?

## Fragen

1. **Anteil erneuerbarer Energien:** Wie hängt der Anteil von der Uhrzeit, vom Wochentag und
   von der Jahreszeit ab? Wie hat er sich seit 2020 entwickelt?
2. **Negative Strompreise:** Wann gibt es negative Preise? Welchen Zusammenhang gibt es mit der
   Residuallast (Last − Wind − PV)?
3. **Prognose der Netzlast:** Wie gut ist eine einfache Prognose für den nächsten Tag?
   Ich vergleiche eine naive Baseline (gleiche Stunde in der Vorwoche) mit einem Modell aus
   scikit-learn. Fehlermaße: MAE und MAPE.
4. **Datenqualität:** Gibt es Lücken oder Ausreißer? Wie gehe ich mit der Zeitumstellung um
   (Tage mit 23 und 25 Stunden)?

## Daten

- **Quelle:** [SMARD](https://www.smard.de), die Strommarktdaten der Bundesnetzagentur
- **Zeitraum:** 1. Januar 2020 bis heute, stündlich, Deutschland
- **Inhalt:** Netzlast, Stromerzeugung nach Energieträger (Photovoltaik, Wind Onshore,
  Wind Offshore, Biomasse, Wasserkraft, Braunkohle, Steinkohle, Erdgas, Kernenergie u. a.)
  und Großhandelspreis Deutschland/Luxemburg
- **Download:** automatisch über die JSON-Schnittstelle von SMARD

### Lizenz und Quellenangabe

Die Marktdaten von SMARD stehen unter der Lizenz
[Creative Commons Namensnennung 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.de).

Quelle: **Bundesnetzagentur | SMARD.de**

**Hinweis zu den Großhandelspreisen:** Laut SMARD wird die Lizenz der Großhandelspreise im
Moment rechtlich geprüft (Festlegungsverfahren HEDWIG). Bis auf Weiteres sollen diese Preise
nicht weiterverwendet werden ([SMARD – Datennutzung](https://www.smard.de/home/datennutzung)).
Deshalb enthält dieses Repository **keine Rohdaten**. Jede Person lädt die Daten selbst mit
dem Skript herunter. Zu den Preisen zeige ich nur zusammengefasste Ergebnisse.

## Projektstruktur (geplant)

```
├── data/              # heruntergeladene Daten und SQLite-Datenbank (nicht im Repository)
├── figures/           # Grafiken für dieses README
├── sql/               # SQL-Abfragen
├── src/               # Python-Skripte: Download, Bereinigung, Analyse, Prognose, Dashboard
├── tests/             # Tests mit pytest
├── requirements.txt
└── README.md
```

## Installation

Voraussetzung: Python 3.14 (getestet unter Windows 10)

```bash
git clone https://github.com/adriancrg/energiewende-in-daten.git
cd energiewende-in-daten
python -m venv .venv
```

Virtuelle Umgebung aktivieren:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

Pakete installieren:

```bash
pip install -r requirements.txt
```

## Ausführen

**1. Daten herunterladen**

```bash
python src/download.py
```

Das Skript lädt alle Zeitreihen von SMARD herunter und speichert sie in `data/`.
Beim ersten Mal dauert das etwa 15 Minuten. Danach lädt das Skript nur neue oder
unvollständige Wochen herunter.

**2. Daten bereinigen und prüfen**

```bash
python src/clean.py
```

Das Skript prüft die Datenqualität (Lücken, Ausreißer, Zeitumstellung), zeigt einen
Bericht in der Konsole und speichert die bereinigten Daten in `data/smard_hourly_clean.csv`.

**3. Datenbank erstellen und SQL-Abfragen ausführen**

```bash
python src/database.py
```

Das Skript erstellt die SQLite-Datenbank `data/energy.db` und führt die SQL-Abfragen aus
dem Ordner `sql/` aus (Anteil erneuerbarer Energien, negative Preise, Datenqualität).

**4. Analyse und Grafiken**

```bash
python src/analysis.py
```

Das Skript erstellt die Grafiken zu den Fragen 1 und 2 im Ordner `figures/`.

**5. Prognose der Netzlast**

```bash
python src/forecast.py
```

Das Skript trainiert das Modell mit den Daten 2020–2024, testet es mit den Daten ab 2025
und vergleicht es mit der Baseline (MAE und MAPE).

Weitere Schritte folgen.

## Ergebnisse

Folgen.

## Werkzeuge

Python, pandas, matplotlib, SQLite, scikit-learn, Streamlit, pytest, Git

---

Entwickelt mit KI-gestützten Werkzeugen; Konzept, Analyse und Interpretation von mir.
