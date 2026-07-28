"""Zentrale Konfiguration der Anwendung EquiBalance."""

from pathlib import Path

APP_NAME = "EquiBalance"
APP_VERSION = "1.0.0"

# Datenbank wird im Benutzerprofil abgelegt (Windows: %USERPROFILE%\EquiBalance)
DATA_DIR = Path.home() / "EquiBalance"
DB_PATH = DATA_DIR / "equibalance.db"

# Fachliche Parameter (Geschäftsregeln GR-09 bis GR-13)
ANALYSE_ZEITRAUM_TAGE = 21          # GR-09, GR-10, GR-13
EINSEITIGKEIT_SCHWELLE = 0.70       # GR-10: Anteil > 70 %
REGENERATION_TAGE_HOCH = 3          # GR-11: 3 Tage hohe Intensität in Folge
SCHWERPUNKT_VERNACHLAESSIGT = 0.5   # GR-12: < 50 % des Durchschnitts

INTENSITAETEN = ["niedrig", "mittel", "hoch"]
GESCHLECHTER = ["Stute", "Wallach", "Hengst"]

STANDARD_TRAININGSARTEN = [
    "Dressur",
    "Springen",
    "Bodenarbeit",
    "Gelände",
    "Cavaletti",
    "Longieren",
    "Freispringen",
]

STANDARD_SCHWERPUNKTE = [
    "Losgelassenheit",
    "Takt",
    "Geraderichtung",
    "Versammlung",
    "Kondition",
    "Koordination",
]

# Farbschema der Oberfläche
COLORS = {
    "bg": "#f4f1ec",
    "surface": "#ffffff",
    "sidebar": "#2f4131",
    "sidebar_active": "#48664b",
    "sidebar_fg": "#e8eee6",
    "primary": "#5b7f5e",
    "accent": "#c08a4a",
    "text": "#2b2b28",
    "muted": "#6f6f68",
    "danger": "#a4413a",
    "border": "#ddd7cd",
}

CHART_COLORS = [
    "#5b7f5e", "#c08a4a", "#7a9e9f", "#a4413a",
    "#8d7b68", "#4f6d7a", "#b3925c", "#6b8f71",
]
