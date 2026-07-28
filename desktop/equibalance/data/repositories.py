"""Repositories: Datenzugriffsschicht für die Geschäftsobjekte (CRUD)."""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import List, Optional

from ..models import Pferd, Schwerpunkt, Trainingsart, Trainingseinheit


def _to_date(value: str) -> date:
    return date.fromisoformat(value)


class PferdRepository:
    """Datenzugriff für das Geschäftsobjekt Pferd (FA-01 bis FA-03, FA-16)."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    @staticmethod
    def _map(row: sqlite3.Row) -> Pferd:
        return Pferd(
            pferd_id=row["pferd_id"],
            name=row["name"],
            geburtsjahr=row["geburtsjahr"],
            rasse=row["rasse"] or "",
            geschlecht=row["geschlecht"] or "",
            archiviert=bool(row["archiviert"]),
        )

    def liste(self, inklusive_archiviert: bool = False) -> List[Pferd]:
        sql = "SELECT * FROM pferd"
        if not inklusive_archiviert:
            sql += " WHERE archiviert = 0"
        sql += " ORDER BY archiviert, name COLLATE NOCASE"
        return [self._map(r) for r in self.connection.execute(sql)]

    def lade(self, pferd_id: int) -> Optional[Pferd]:
        row = self.connection.execute(
            "SELECT * FROM pferd WHERE pferd_id = ?", (pferd_id,)
        ).fetchone()
        return self._map(row) if row else None

    def anlegen(self, pferd: Pferd) -> Pferd:
        cur = self.connection.execute(
            "INSERT INTO pferd (name, geburtsjahr, rasse, geschlecht, archiviert)"
            " VALUES (?, ?, ?, ?, ?)",
            (pferd.name, pferd.geburtsjahr, pferd.rasse, pferd.geschlecht,
             int(pferd.archiviert)),
        )
        self.connection.commit()
        pferd.pferd_id = cur.lastrowid
        return pferd

    def aktualisieren(self, pferd: Pferd) -> None:
        self.connection.execute(
            "UPDATE pferd SET name = ?, geburtsjahr = ?, rasse = ?, geschlecht = ?,"
            " archiviert = ? WHERE pferd_id = ?",
            (pferd.name, pferd.geburtsjahr, pferd.rasse, pferd.geschlecht,
             int(pferd.archiviert), pferd.pferd_id),
        )
        self.connection.commit()

    def archivieren(self, pferd_id: int, archiviert: bool = True) -> None:
        self.connection.execute(
            "UPDATE pferd SET archiviert = ? WHERE pferd_id = ?",
            (int(archiviert), pferd_id),
        )
        self.connection.commit()

    def loeschen(self, pferd_id: int) -> None:
        self.connection.execute("DELETE FROM pferd WHERE pferd_id = ?", (pferd_id,))
        self.connection.commit()


class StammdatenRepository:
    """Datenzugriff für Trainingsarten und Schwerpunkte."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def trainingsarten(self) -> List[Trainingsart]:
        rows = self.connection.execute(
            "SELECT * FROM trainingsart ORDER BY bezeichnung COLLATE NOCASE"
        )
        return [Trainingsart(r["trainingsart_id"], r["bezeichnung"]) for r in rows]

    def schwerpunkte(self) -> List[Schwerpunkt]:
        rows = self.connection.execute(
            "SELECT * FROM schwerpunkt ORDER BY bezeichnung COLLATE NOCASE"
        )
        return [Schwerpunkt(r["schwerpunkt_id"], r["bezeichnung"]) for r in rows]


class TrainingRepository:
    """Datenzugriff für Trainingseinheiten (FA-04 bis FA-08, FA-17)."""

    BASE_SQL = """
        SELECT t.*, a.bezeichnung AS art_bezeichnung, s.bezeichnung AS sp_bezeichnung
        FROM trainingseinheit t
        JOIN trainingsart a ON a.trainingsart_id = t.trainingsart_id
        JOIN schwerpunkt  s ON s.schwerpunkt_id  = t.schwerpunkt_id
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    @staticmethod
    def _map(row: sqlite3.Row) -> Trainingseinheit:
        return Trainingseinheit(
            training_id=row["training_id"],
            pferd_id=row["pferd_id"],
            datum=_to_date(row["datum"]),
            dauer=row["dauer"],
            intensitaet=row["intensitaet"],
            trainingsart_id=row["trainingsart_id"],
            schwerpunkt_id=row["schwerpunkt_id"],
            trainingsort=row["trainingsort"] or "",
            wetter=row["wetter"] or "",
            notizen=row["notizen"] or "",
            trainingsart=row["art_bezeichnung"],
            schwerpunkt=row["sp_bezeichnung"],
        )

    def liste_fuer_pferd(
        self,
        pferd_id: int,
        von: Optional[date] = None,
        bis: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[Trainingseinheit]:
        sql = self.BASE_SQL + " WHERE t.pferd_id = ?"
        params: list = [pferd_id]
        if von:
            sql += " AND t.datum >= ?"
            params.append(von.isoformat())
        if bis:
            sql += " AND t.datum <= ?"
            params.append(bis.isoformat())
        sql += " ORDER BY t.datum DESC, t.training_id DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        return [self._map(r) for r in self.connection.execute(sql, params)]

    def lade(self, training_id: int) -> Optional[Trainingseinheit]:
        row = self.connection.execute(
            self.BASE_SQL + " WHERE t.training_id = ?", (training_id,)
        ).fetchone()
        return self._map(row) if row else None

    def anlegen(self, einheit: Trainingseinheit) -> Trainingseinheit:
        cur = self.connection.execute(
            "INSERT INTO trainingseinheit (pferd_id, datum, dauer, intensitaet,"
            " trainingsart_id, schwerpunkt_id, trainingsort, wetter, notizen)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                einheit.pferd_id, einheit.datum.isoformat(), einheit.dauer,
                einheit.intensitaet, einheit.trainingsart_id, einheit.schwerpunkt_id,
                einheit.trainingsort, einheit.wetter, einheit.notizen,
            ),
        )
        self.connection.commit()
        einheit.training_id = cur.lastrowid
        return einheit

    def aktualisieren(self, einheit: Trainingseinheit) -> None:
        self.connection.execute(
            "UPDATE trainingseinheit SET datum = ?, dauer = ?, intensitaet = ?,"
            " trainingsart_id = ?, schwerpunkt_id = ?, trainingsort = ?, wetter = ?,"
            " notizen = ? WHERE training_id = ?",
            (
                einheit.datum.isoformat(), einheit.dauer, einheit.intensitaet,
                einheit.trainingsart_id, einheit.schwerpunkt_id, einheit.trainingsort,
                einheit.wetter, einheit.notizen, einheit.training_id,
            ),
        )
        self.connection.commit()

    def loeschen(self, training_id: int) -> None:
        self.connection.execute(
            "DELETE FROM trainingseinheit WHERE training_id = ?", (training_id,)
        )
        self.connection.commit()
