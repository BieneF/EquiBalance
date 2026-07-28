"""Tests der Datenzugriffsschicht mit temporärer SQLite-Datenbank."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from equibalance.data import (
    Database,
    PferdRepository,
    StammdatenRepository,
    TrainingRepository,
)
from equibalance.models import Pferd, Trainingseinheit


class RepositoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.db")
        self.pferde = PferdRepository(self.db.connection)
        self.trainings = TrainingRepository(self.db.connection)
        self.stammdaten = StammdatenRepository(self.db.connection)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_stammdaten_vorhanden(self):
        self.assertEqual(len(self.stammdaten.trainingsarten()), 7)
        self.assertEqual(len(self.stammdaten.schwerpunkte()), 6)

    def test_crud_pferd(self):
        pferd = self.pferde.anlegen(Pferd(name="Balou", geburtsjahr=2014))
        self.assertIsNotNone(pferd.pferd_id)

        pferd.rasse = "Hannoveraner"
        self.pferde.aktualisieren(pferd)
        self.assertEqual(self.pferde.lade(pferd.pferd_id).rasse, "Hannoveraner")

        self.pferde.archivieren(pferd.pferd_id, True)
        self.assertEqual(len(self.pferde.liste()), 0)
        self.assertEqual(len(self.pferde.liste(inklusive_archiviert=True)), 1)

    def test_crud_training_und_filter(self):
        pferd = self.pferde.anlegen(Pferd(name="Fee"))
        art = self.stammdaten.trainingsarten()[0]
        sp = self.stammdaten.schwerpunkte()[0]

        for tage in (0, 10, 40):
            self.trainings.anlegen(
                Trainingseinheit(
                    pferd_id=pferd.pferd_id,
                    datum=date.today() - timedelta(days=tage),
                    dauer=45,
                    intensitaet="mittel",
                    trainingsart_id=art.trainingsart_id,
                    schwerpunkt_id=sp.schwerpunkt_id,
                )
            )

        alle = self.trainings.liste_fuer_pferd(pferd.pferd_id)
        self.assertEqual(len(alle), 3)

        gefiltert = self.trainings.liste_fuer_pferd(
            pferd.pferd_id, von=date.today() - timedelta(days=20)
        )
        self.assertEqual(len(gefiltert), 2)

        eintrag = alle[0]
        eintrag.dauer = 60
        self.trainings.aktualisieren(eintrag)
        self.assertEqual(self.trainings.lade(eintrag.training_id).dauer, 60)

        self.trainings.loeschen(eintrag.training_id)
        self.assertEqual(len(self.trainings.liste_fuer_pferd(pferd.pferd_id)), 2)


if __name__ == "__main__":
    unittest.main()
