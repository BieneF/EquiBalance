"""Erzeugt Beispieldaten zum Ausprobieren der Anwendung.

Aufruf:  python demo_daten.py
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from equibalance.data import Database, PferdRepository, StammdatenRepository, TrainingRepository
from equibalance.models import Pferd, Trainingseinheit


def main() -> None:
    db = Database()
    pferde = PferdRepository(db.connection)
    stammdaten = StammdatenRepository(db.connection)
    trainings = TrainingRepository(db.connection)

    if pferde.liste(inklusive_archiviert=True):
        print("Es sind bereits Daten vorhanden – es werden keine Demodaten angelegt.")
        return

    arten = stammdaten.trainingsarten()
    schwerpunkte = stammdaten.schwerpunkte()

    balou = pferde.anlegen(
        Pferd(name="Balou", geburtsjahr=2014, rasse="Hannoveraner", geschlecht="Wallach")
    )
    fee = pferde.anlegen(
        Pferd(name="Fee", geburtsjahr=2011, rasse="Haflinger", geschlecht="Stute")
    )

    zufall = random.Random(42)
    heute = date.today()

    # Balou: überwiegend Dressur (löst GR-10 und GR-09 aus)
    for tag in range(0, 40, 2):
        art = arten[0] if zufall.random() < 0.8 else zufall.choice(arten[:4])
        trainings.anlegen(
            Trainingseinheit(
                pferd_id=balou.pferd_id,
                datum=heute - timedelta(days=tag),
                dauer=zufall.choice([30, 40, 45, 50, 60]),
                intensitaet=zufall.choice(["niedrig", "mittel", "mittel", "hoch"]),
                trainingsart_id=art.trainingsart_id,
                schwerpunkt_id=zufall.choice(schwerpunkte[:3]).schwerpunkt_id,
                trainingsort=zufall.choice(["Reithalle", "Außenplatz", "Gelände"]),
                wetter=zufall.choice(["sonnig", "bewölkt", "regnerisch"]),
                notizen="",
            )
        )

    # Fee: drei intensive Tage in Folge (löst GR-11 aus)
    for tag in range(0, 3):
        trainings.anlegen(
            Trainingseinheit(
                pferd_id=fee.pferd_id,
                datum=heute - timedelta(days=tag),
                dauer=55,
                intensitaet="hoch",
                trainingsart_id=arten[tag % len(arten)].trainingsart_id,
                schwerpunkt_id=schwerpunkte[tag % len(schwerpunkte)].schwerpunkt_id,
                trainingsort="Außenplatz",
                wetter="sonnig",
                notizen="Intensive Einheit",
            )
        )

    print("Demodaten wurden angelegt.")
    db.close()


if __name__ == "__main__":
    main()
