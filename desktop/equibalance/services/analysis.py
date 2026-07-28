"""Analysefunktionen: Statistiken, Verteilungen, Trainingslücken, Ausgewogenheit.

Umsetzung der funktionalen Anforderungen FA-09 bis FA-14 sowie GR-08 und GR-13.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List

from ..config import ANALYSE_ZEITRAUM_TAGE
from ..models import Trainingseinheit


@dataclass
class Analyseergebnis:
    """Bündelt alle berechneten Kennzahlen eines Pferdes."""

    zeitraum_tage: int = ANALYSE_ZEITRAUM_TAGE
    anzahl_gesamt: int = 0
    anzahl_zeitraum: int = 0
    minuten_gesamt: int = 0
    minuten_zeitraum: int = 0
    durchschnittsdauer: float = 0.0
    haeufigkeit_pro_woche: float = 0.0
    letztes_training: date | None = None
    tage_seit_letztem_training: int | None = None
    verteilung_arten: Dict[str, int] = field(default_factory=dict)
    verteilung_schwerpunkte: Dict[str, int] = field(default_factory=dict)
    verteilung_intensitaet: Dict[str, int] = field(default_factory=dict)
    minuten_pro_woche: Dict[str, int] = field(default_factory=dict)
    trainingsluecken: List[str] = field(default_factory=list)
    ausgewogenheitsindex: float = 0.0


class AnalyseService:
    """Berechnet Statistiken auf Basis der Trainingseinheiten eines Pferdes."""

    def __init__(self, zeitraum_tage: int = ANALYSE_ZEITRAUM_TAGE) -> None:
        self.zeitraum_tage = zeitraum_tage

    # ------------------------------------------------------------------ Helfer
    def _zeitraum_start(self, stichtag: date) -> date:
        return stichtag - timedelta(days=self.zeitraum_tage - 1)

    @staticmethod
    def einheiten_im_zeitraum(
        einheiten: List[Trainingseinheit], von: date, bis: date
    ) -> List[Trainingseinheit]:
        return [e for e in einheiten if von <= e.datum <= bis]

    # ----------------------------------------------------------- Kernfunktion
    def analysiere(
        self,
        einheiten: List[Trainingseinheit],
        alle_trainingsarten: List[str],
        stichtag: date | None = None,
    ) -> Analyseergebnis:
        stichtag = stichtag or date.today()
        ergebnis = Analyseergebnis(zeitraum_tage=self.zeitraum_tage)

        if not einheiten:
            ergebnis.trainingsluecken = list(alle_trainingsarten)
            return ergebnis

        von = self._zeitraum_start(stichtag)
        zeitraum = self.einheiten_im_zeitraum(einheiten, von, stichtag)

        ergebnis.anzahl_gesamt = len(einheiten)
        ergebnis.anzahl_zeitraum = len(zeitraum)
        ergebnis.minuten_gesamt = sum(e.dauer for e in einheiten)
        ergebnis.minuten_zeitraum = sum(e.dauer for e in zeitraum)
        ergebnis.durchschnittsdauer = round(
            ergebnis.minuten_gesamt / ergebnis.anzahl_gesamt, 1
        )                                                            # FA-10
        ergebnis.haeufigkeit_pro_woche = round(
            len(zeitraum) / (self.zeitraum_tage / 7), 2
        )                                                            # FA-09

        ergebnis.letztes_training = max(e.datum for e in einheiten)
        ergebnis.tage_seit_letztem_training = (
            stichtag - ergebnis.letztes_training
        ).days

        ergebnis.verteilung_arten = dict(                            # FA-11
            Counter(e.trainingsart for e in zeitraum).most_common()
        )
        ergebnis.verteilung_schwerpunkte = dict(
            Counter(e.schwerpunkt for e in zeitraum).most_common()
        )
        ergebnis.verteilung_intensitaet = dict(
            Counter(e.intensitaet for e in zeitraum)
        )
        ergebnis.minuten_pro_woche = self._minuten_pro_woche(einheiten, stichtag)
        ergebnis.trainingsluecken = self.finde_trainingsluecken(   # FA-12
            zeitraum, alle_trainingsarten
        )
        ergebnis.ausgewogenheitsindex = self.ausgewogenheitsindex(  # GR-13
            ergebnis.verteilung_arten
        )
        return ergebnis

    # --------------------------------------------------------- Einzelmetriken
    @staticmethod
    def _minuten_pro_woche(
        einheiten: List[Trainingseinheit], stichtag: date, wochen: int = 8
    ) -> Dict[str, int]:
        """Trainingsminuten der letzten Wochen (für das Balkendiagramm)."""
        buckets: Dict[str, int] = {}
        for i in range(wochen - 1, -1, -1):
            ende = stichtag - timedelta(days=7 * i)
            start = ende - timedelta(days=6)
            label = start.strftime("%d.%m.")
            buckets[label] = sum(
                e.dauer for e in einheiten if start <= e.datum <= ende
            )
        return buckets

    @staticmethod
    def finde_trainingsluecken(
        zeitraum_einheiten: List[Trainingseinheit], alle_trainingsarten: List[str]
    ) -> List[str]:
        """GR-09: Trainingsarten, die im Zeitraum nicht dokumentiert wurden."""
        trainiert = {e.trainingsart for e in zeitraum_einheiten}
        return [art for art in alle_trainingsarten if art not in trainiert]

    @staticmethod
    def ausgewogenheitsindex(verteilung: Dict[str, int]) -> float:
        """GR-13: normierte Shannon-Entropie der Trainingsarten (0-100).

        100 bedeutet eine völlig gleichmäßige Verteilung der Trainingsarten,
        0 bedeutet, dass ausschließlich eine einzige Trainingsart trainiert wurde.
        """
        gesamt = sum(verteilung.values())
        if gesamt == 0:
            return 0.0
        if len(verteilung) == 1:
            return 0.0
        entropie = -sum(
            (n / gesamt) * math.log(n / gesamt) for n in verteilung.values() if n
        )
        max_entropie = math.log(len(verteilung))
        return round((entropie / max_entropie) * 100, 1)
