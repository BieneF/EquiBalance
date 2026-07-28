"""Regelbasiertes Empfehlungssystem (Geschäftsregeln GR-07 bis GR-13).

Die Empfehlungen werden ausschließlich zur Laufzeit aus den vorhandenen
Trainingseinheiten berechnet und nicht dauerhaft gespeichert (GR-07).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List

from ..config import (
    ANALYSE_ZEITRAUM_TAGE,
    EINSEITIGKEIT_SCHWELLE,
    REGENERATION_TAGE_HOCH,
    SCHWERPUNKT_VERNACHLAESSIGT,
)
from ..models import Trainingseinheit


@dataclass
class Empfehlung:
    """Eine einzelne, nachvollziehbare Trainingsempfehlung."""

    regel: str          # z. B. "GR-09"
    kategorie: str      # Trainingslücke, Einseitigkeit, Regeneration, ...
    titel: str
    text: str
    prioritaet: str     # hoch | mittel | niedrig


class EmpfehlungsService:
    """Wendet die definierten Geschäftsregeln auf die Trainingsdaten an."""

    def __init__(self, zeitraum_tage: int = ANALYSE_ZEITRAUM_TAGE) -> None:
        self.zeitraum_tage = zeitraum_tage

    def erzeuge(
        self,
        einheiten: List[Trainingseinheit],
        alle_trainingsarten: List[str],
        alle_schwerpunkte: List[str],
        stichtag: date | None = None,
    ) -> List[Empfehlung]:
        stichtag = stichtag or date.today()
        von = stichtag - timedelta(days=self.zeitraum_tage - 1)
        zeitraum = [e for e in einheiten if von <= e.datum <= stichtag]

        empfehlungen: List[Empfehlung] = []

        if not einheiten:
            empfehlungen.append(
                Empfehlung(
                    regel="—",
                    kategorie="Einstieg",
                    titel="Noch keine Trainingsdaten vorhanden",
                    text=(
                        "Erfassen Sie die erste Trainingseinheit, damit EquiBalance "
                        "Auswertungen und Empfehlungen berechnen kann."
                    ),
                    prioritaet="niedrig",
                )
            )
            return empfehlungen

        empfehlungen += self._regel_09_trainingsluecken(zeitraum, alle_trainingsarten)
        empfehlungen += self._regel_10_einseitigkeit(zeitraum)
        empfehlungen += self._regel_11_regeneration(einheiten, stichtag)
        empfehlungen += self._regel_12_schwerpunkte(zeitraum, alle_schwerpunkte)
        empfehlungen += self._regel_pausenhinweis(einheiten, stichtag)

        if not empfehlungen:
            empfehlungen.append(
                Empfehlung(
                    regel="—",
                    kategorie="Bestätigung",
                    titel="Das Training ist derzeit ausgewogen",
                    text=(
                        f"In den letzten {self.zeitraum_tage} Tagen wurden Trainings"
                        "arten, Schwerpunkte und Belastung ausgewogen verteilt. "
                        "Behalten Sie die aktuelle Trainingsgestaltung bei."
                    ),
                    prioritaet="niedrig",
                )
            )
        return empfehlungen

    # ------------------------------------------------------------------ GR-09
    def _regel_09_trainingsluecken(
        self, zeitraum: List[Trainingseinheit], alle_arten: List[str]
    ) -> List[Empfehlung]:
        trainiert = {e.trainingsart for e in zeitraum}
        fehlend = [a for a in alle_arten if a not in trainiert]
        if not fehlend:
            return []
        return [
            Empfehlung(
                regel="GR-09",
                kategorie="Trainingslücke",
                titel=f"{len(fehlend)} Trainingsart(en) länger nicht trainiert",
                text=(
                    f"{', '.join(fehlend)} wurde(n) in den letzten "
                    f"{self.zeitraum_tage} Tagen nicht dokumentiert. Planen Sie diese "
                    "Trainingsform wieder ein, um das Training vielseitig zu halten."
                ),
                prioritaet="mittel",
            )
        ]

    # ------------------------------------------------------------------ GR-10
    def _regel_10_einseitigkeit(
        self, zeitraum: List[Trainingseinheit]
    ) -> List[Empfehlung]:
        if not zeitraum:
            return []
        verteilung: Dict[str, int] = Counter(e.trainingsart for e in zeitraum)
        gesamt = sum(verteilung.values())
        art, anzahl = verteilung.most_common(1)[0]
        anteil = anzahl / gesamt
        if anteil <= EINSEITIGKEIT_SCHWELLE:
            return []
        return [
            Empfehlung(
                regel="GR-10",
                kategorie="Einseitigkeit",
                titel=f"{art} dominiert das Training",
                text=(
                    f"{art} macht {anteil * 100:.0f} % aller Einheiten der letzten "
                    f"{self.zeitraum_tage} Tage aus (Schwellenwert "
                    f"{EINSEITIGKEIT_SCHWELLE * 100:.0f} %). Mehr Abwechslung "
                    "entlastet das Pferd und fördert eine vielseitige Ausbildung."
                ),
                prioritaet="hoch",
            )
        ]

    # ------------------------------------------------------------------ GR-11
    def _regel_11_regeneration(
        self, einheiten: List[Trainingseinheit], stichtag: date
    ) -> List[Empfehlung]:
        hohe_tage = sorted({e.datum for e in einheiten if e.intensitaet == "hoch"})
        if len(hohe_tage) < REGENERATION_TAGE_HOCH:
            return []

        serie = 1
        letzte_serie_ende = None
        for i in range(1, len(hohe_tage)):
            if (hohe_tage[i] - hohe_tage[i - 1]).days == 1:
                serie += 1
            else:
                serie = 1
            if serie >= REGENERATION_TAGE_HOCH:
                letzte_serie_ende = hohe_tage[i]

        if letzte_serie_ende is None:
            return []
        if (stichtag - letzte_serie_ende).days > 2:
            return []
        return [
            Empfehlung(
                regel="GR-11",
                kategorie="Regeneration",
                titel="Regenerationstag empfohlen",
                text=(
                    f"An {REGENERATION_TAGE_HOCH} aufeinanderfolgenden Tagen "
                    f"(zuletzt am {letzte_serie_ende.strftime('%d.%m.%Y')}) wurde mit "
                    "hoher Intensität trainiert. Planen Sie einen Ruhetag oder eine "
                    "leichte Einheit ein."
                ),
                prioritaet="hoch",
            )
        ]

    # ------------------------------------------------------------------ GR-12
    def _regel_12_schwerpunkte(
        self, zeitraum: List[Trainingseinheit], alle_schwerpunkte: List[str]
    ) -> List[Empfehlung]:
        if len(zeitraum) < 5:
            return []
        zaehler: Dict[str, int] = {sp: 0 for sp in alle_schwerpunkte}
        for e in zeitraum:
            zaehler[e.schwerpunkt] = zaehler.get(e.schwerpunkt, 0) + 1
        if not zaehler:
            return []
        durchschnitt = sum(zaehler.values()) / len(zaehler)
        vernachlaessigt = [
            sp for sp, n in zaehler.items()
            if n < durchschnitt * SCHWERPUNKT_VERNACHLAESSIGT
        ]
        if not vernachlaessigt:
            return []
        return [
            Empfehlung(
                regel="GR-12",
                kategorie="Schwerpunkt",
                titel="Einzelne Schwerpunkte werden selten trainiert",
                text=(
                    f"{', '.join(sorted(vernachlaessigt))} wurde(n) deutlich seltener "
                    "trainiert als die übrigen Schwerpunkte. Berücksichtigen Sie "
                    "diese Ziele in den kommenden Einheiten stärker."
                ),
                prioritaet="mittel",
            )
        ]

    # ----------------------------------------------------- ergänzender Hinweis
    def _regel_pausenhinweis(
        self, einheiten: List[Trainingseinheit], stichtag: date
    ) -> List[Empfehlung]:
        letztes = max(e.datum for e in einheiten)
        tage = (stichtag - letztes).days
        if tage < 10:
            return []
        return [
            Empfehlung(
                regel="GR-09",
                kategorie="Trainingspause",
                titel=f"Seit {tage} Tagen keine Einheit dokumentiert",
                text=(
                    f"Die letzte Trainingseinheit wurde am "
                    f"{letztes.strftime('%d.%m.%Y')} erfasst. Nach längeren Pausen "
                    "empfiehlt sich ein langsamer Wiedereinstieg."
                ),
                prioritaet="mittel",
            )
        ]
