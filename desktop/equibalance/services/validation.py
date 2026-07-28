"""Eingabevalidierung und Geschäftsregeln GR-01 bis GR-08."""

from __future__ import annotations

from datetime import date
from typing import List

from ..config import INTENSITAETEN
from ..models import Pferd, Trainingseinheit


class ValidierungsFehler(Exception):
    """Sammelt fachliche Validierungsfehler."""

    def __init__(self, fehler: List[str]) -> None:
        super().__init__("\n".join(fehler))
        self.fehler = fehler


def validiere_pferd(pferd: Pferd) -> None:
    fehler: List[str] = []
    if not pferd.name.strip():
        fehler.append("Der Name des Pferdes ist ein Pflichtfeld.")
    if pferd.geburtsjahr is not None:
        if pferd.geburtsjahr < 1980 or pferd.geburtsjahr > date.today().year:
            fehler.append(
                f"Das Geburtsjahr muss zwischen 1980 und {date.today().year} liegen."
            )
    if fehler:
        raise ValidierungsFehler(fehler)


def validiere_trainingseinheit(einheit: Trainingseinheit, pferd: Pferd) -> None:
    """Prüft die Geschäftsregeln GR-01 bis GR-06."""
    fehler: List[str] = []

    if not einheit.pferd_id:                                    # GR-01
        fehler.append("Die Trainingseinheit muss einem Pferd zugeordnet sein.")
    if pferd is not None and pferd.archiviert:                  # GR-06
        fehler.append(
            "Archivierte Pferde dürfen keine neuen Trainingseinheiten erhalten."
        )
    if einheit.datum is None:                                   # GR-02
        fehler.append("Das Datum ist ein Pflichtfeld.")
    elif einheit.datum > date.today():
        fehler.append("Das Datum darf nicht in der Zukunft liegen.")
    if not einheit.trainingsart_id:                             # GR-03
        fehler.append("Es muss genau eine Trainingsart ausgewählt werden.")
    if not einheit.schwerpunkt_id:                              # GR-04
        fehler.append("Es muss genau ein Schwerpunkt ausgewählt werden.")
    if einheit.dauer is None or einheit.dauer <= 0:             # GR-05
        fehler.append("Die Trainingsdauer muss größer als 0 Minuten sein.")
    elif einheit.dauer > 600:
        fehler.append("Die Trainingsdauer darf 600 Minuten nicht überschreiten.")
    if einheit.intensitaet not in INTENSITAETEN:
        fehler.append("Die Intensität muss aus der Auswahlliste gewählt werden.")

    if fehler:
        raise ValidierungsFehler(fehler)
