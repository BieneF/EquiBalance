"""Tests der Fachlogik (Qualitätssicherung, AP7).

Aufruf:  python -m unittest discover -s tests
"""

from __future__ import annotations

import unittest
from datetime import date, timedelta

from equibalance.models import Pferd, Trainingseinheit
from equibalance.services import (
    AnalyseService,
    EmpfehlungsService,
    ValidierungsFehler,
    validiere_pferd,
    validiere_trainingseinheit,
)

ARTEN = ["Dressur", "Springen", "Bodenarbeit", "Gelände"]
SCHWERPUNKTE = ["Losgelassenheit", "Takt", "Kondition"]


def einheit(tage_zurueck: int, art="Dressur", intensitaet="mittel",
            schwerpunkt="Takt", dauer=45) -> Trainingseinheit:
    return Trainingseinheit(
        training_id=tage_zurueck + 1,
        pferd_id=1,
        datum=date.today() - timedelta(days=tage_zurueck),
        dauer=dauer,
        intensitaet=intensitaet,
        trainingsart_id=1,
        schwerpunkt_id=1,
        trainingsart=art,
        schwerpunkt=schwerpunkt,
    )


class ValidierungTest(unittest.TestCase):
    def test_pferd_ohne_name_ungueltig(self):
        with self.assertRaises(ValidierungsFehler):
            validiere_pferd(Pferd(name="  "))

    def test_dauer_muss_groesser_null_sein(self):  # GR-05
        e = einheit(0, dauer=0)
        with self.assertRaises(ValidierungsFehler):
            validiere_trainingseinheit(e, Pferd(pferd_id=1, name="Balou"))

    def test_archiviertes_pferd_blockiert(self):  # GR-06
        with self.assertRaises(ValidierungsFehler):
            validiere_trainingseinheit(
                einheit(0), Pferd(pferd_id=1, name="Balou", archiviert=True)
            )

    def test_gueltige_einheit(self):
        validiere_trainingseinheit(einheit(0), Pferd(pferd_id=1, name="Balou"))


class AnalyseTest(unittest.TestCase):
    def setUp(self):
        self.service = AnalyseService()

    def test_durchschnittsdauer(self):  # FA-10
        ergebnis = self.service.analysiere(
            [einheit(1, dauer=30), einheit(2, dauer=60)], ARTEN
        )
        self.assertEqual(ergebnis.durchschnittsdauer, 45.0)

    def test_trainingsluecken(self):  # FA-12 / GR-09
        ergebnis = self.service.analysiere([einheit(1, art="Dressur")], ARTEN)
        self.assertNotIn("Dressur", ergebnis.trainingsluecken)
        self.assertIn("Springen", ergebnis.trainingsluecken)

    def test_index_einseitig_ist_null(self):  # GR-13
        einheiten = [einheit(i, art="Dressur") for i in range(5)]
        ergebnis = self.service.analysiere(einheiten, ARTEN)
        self.assertEqual(ergebnis.ausgewogenheitsindex, 0.0)

    def test_index_ausgewogen_ist_hoch(self):
        einheiten = [einheit(i, art=ARTEN[i % 4]) for i in range(8)]
        ergebnis = self.service.analysiere(einheiten, ARTEN)
        self.assertEqual(ergebnis.ausgewogenheitsindex, 100.0)


class EmpfehlungTest(unittest.TestCase):
    def setUp(self):
        self.service = EmpfehlungsService()

    def _regeln(self, einheiten):
        return {
            e.regel
            for e in self.service.erzeuge(einheiten, ARTEN, SCHWERPUNKTE)
        }

    def test_einseitigkeit_gr10(self):
        einheiten = [einheit(i, art="Dressur") for i in range(10)]
        self.assertIn("GR-10", self._regeln(einheiten))

    def test_regeneration_gr11(self):
        einheiten = [einheit(i, intensitaet="hoch") for i in range(3)]
        self.assertIn("GR-11", self._regeln(einheiten))

    def test_keine_regeneration_bei_moderatem_training(self):
        einheiten = [einheit(i * 3, art=ARTEN[i % 4]) for i in range(6)]
        self.assertNotIn("GR-11", self._regeln(einheiten))

    def test_ohne_daten_einstiegshinweis(self):
        empfehlungen = self.service.erzeuge([], ARTEN, SCHWERPUNKTE)
        self.assertEqual(len(empfehlungen), 1)
        self.assertEqual(empfehlungen[0].kategorie, "Einstieg")


if __name__ == "__main__":
    unittest.main()
