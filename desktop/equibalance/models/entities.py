"""Geschäftsobjekte (Datenmodell) der Anwendung EquiBalance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Pferd:
    """Geschäftsobjekt Pferd (Tabelle 9 der Spezifikation)."""

    pferd_id: Optional[int] = None
    name: str = ""
    geburtsjahr: Optional[int] = None
    rasse: str = ""
    geschlecht: str = ""
    archiviert: bool = False

    @property
    def alter(self) -> Optional[int]:
        if not self.geburtsjahr:
            return None
        return date.today().year - self.geburtsjahr

    def __str__(self) -> str:
        return self.name


@dataclass
class Trainingsart:
    """Geschäftsobjekt Trainingsart (Tabelle 11)."""

    trainingsart_id: Optional[int] = None
    bezeichnung: str = ""

    def __str__(self) -> str:
        return self.bezeichnung


@dataclass
class Schwerpunkt:
    """Geschäftsobjekt Schwerpunkt (Tabelle 12)."""

    schwerpunkt_id: Optional[int] = None
    bezeichnung: str = ""

    def __str__(self) -> str:
        return self.bezeichnung


@dataclass
class Trainingseinheit:
    """Geschäftsobjekt Trainingseinheit (Tabelle 10)."""

    training_id: Optional[int] = None
    pferd_id: Optional[int] = None
    datum: Optional[date] = None
    dauer: int = 0
    intensitaet: str = ""
    trainingsart_id: Optional[int] = None
    schwerpunkt_id: Optional[int] = None
    trainingsort: str = ""
    wetter: str = ""
    notizen: str = ""

    # Anzeigefelder (durch Joins befüllt)
    trainingsart: str = field(default="", compare=False)
    schwerpunkt: str = field(default="", compare=False)
