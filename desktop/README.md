# EquiBalance – Windows-Desktopanwendung

Trainingsdokumentation, Analyse und regelbasierte Empfehlungen für Pferdebesitzer:innen
und Reitbeteiligungen. Umsetzung der Spezifikation aus dem Portfolio-Dokument
(Phase 1) in Python.

## Technik

| Bereich        | Umsetzung                                       |
| -------------- | ----------------------------------------------- |
| Sprache        | Python 3.10+                                    |
| Oberfläche     | Tkinter / ttk (Standardbibliothek)              |
| Datenhaltung   | SQLite (Standardbibliothek)                     |
| Diagramme      | selbst gezeichnet auf `tk.Canvas` (keine Abhängigkeiten) |
| Architektur    | Schichtenmodell: UI – Services – Repositories – Datenbank |

Es werden **keine externen Bibliotheken** benötigt (NFA-10: kein Internetzugang nötig).

## Start

```bash
cd desktop
python main.py
```

Optional Beispieldaten anlegen:

```bash
python demo_daten.py
```

Die Datenbank liegt unter `%USERPROFILE%\EquiBalance\equibalance.db`.

## Tests

```bash
cd desktop
python -m unittest discover -s tests -v
```

## Projektstruktur

```
desktop/
├── main.py                     Startpunkt
├── demo_daten.py               Beispieldatensatz
├── equibalance/
│   ├── config.py               Konstanten, Geschäftsregel-Parameter, Farbschema
│   ├── models/entities.py      Geschäftsobjekte (Pferd, Trainingseinheit, ...)
│   ├── data/database.py        SQLite-Verbindung, Schema, Stammdaten
│   ├── data/repositories.py    CRUD-Zugriff
│   ├── services/validation.py  Eingabevalidierung, GR-01 bis GR-06
│   ├── services/analysis.py    Statistiken, Trainingslücken, Ausgewogenheitsindex
│   ├── services/recommendations.py  Regelbasiertes Empfehlungssystem GR-09 bis GR-13
│   ├── widgets_helpers.py      Formatierungshelfer
│   └── ui/                     Dashboard, Pferde-, Trainings-, Analyse-, Empfehlungsansicht
└── tests/                      Unittests der Fachlogik und Datenschicht
```

## Abdeckung der Anforderungen

| Anforderung        | Umsetzung |
| ------------------ | --------- |
| FA-01 – FA-03, FA-16 | Pferdeverwaltung: anlegen, bearbeiten, archivieren, archivierte ein-/ausblenden |
| FA-04 – FA-06      | Trainingseinheiten erfassen, bearbeiten, löschen |
| FA-07, NFA-03/09   | Persistenz in SQLite |
| FA-08, FA-17       | Trainingsliste je Pferd mit Zeitraumfilter |
| FA-09 – FA-12      | Häufigkeit, Ø-Dauer, Verteilung der Trainingsarten, Trainingslücken |
| FA-13              | Empfehlungen aus GR-09 bis GR-13 |
| FA-14              | Balken-, Säulen-, Ring-, Index- und Kalenderdiagramme |
| FA-15              | Dashboard mit Kennzahlen, letzten Einheiten und Hinweisen |
| GR-01 – GR-06      | Validierung vor dem Speichern (`services/validation.py`) |
| GR-07              | Empfehlungen werden zur Laufzeit berechnet, nicht gespeichert |
| GR-08              | Analyse immer nur für das aktuell gewählte Pferd |
| GR-13              | Ausgewogenheitsindex als normierte Shannon-Entropie (0–100) |
| NFA-05, NFA-08     | Modulare, objektorientierte, dokumentierte Schichtenarchitektur |

## Als Windows-EXE paketieren

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --onefile --name EquiBalance main.py
```

Das Ergebnis liegt unter `dist/EquiBalance.exe` und läuft unter Windows 10/11 (NFA-01).
