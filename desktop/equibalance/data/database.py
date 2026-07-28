"""Datenbankzugriff: Verbindung, Schema und Stammdaten (SQLite)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from ..config import DB_PATH, STANDARD_SCHWERPUNKTE, STANDARD_TRAININGSARTEN

SCHEMA = """
CREATE TABLE IF NOT EXISTS pferd (
    pferd_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    geburtsjahr  INTEGER,
    rasse        TEXT,
    geschlecht   TEXT,
    archiviert   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS trainingsart (
    trainingsart_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bezeichnung     TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS schwerpunkt (
    schwerpunkt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bezeichnung    TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS trainingseinheit (
    training_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    pferd_id        INTEGER NOT NULL REFERENCES pferd(pferd_id) ON DELETE CASCADE,
    datum           TEXT    NOT NULL,
    dauer           INTEGER NOT NULL CHECK (dauer > 0),
    intensitaet     TEXT    NOT NULL,
    trainingsart_id INTEGER NOT NULL REFERENCES trainingsart(trainingsart_id),
    schwerpunkt_id  INTEGER NOT NULL REFERENCES schwerpunkt(schwerpunkt_id),
    trainingsort    TEXT,
    wetter          TEXT,
    notizen         TEXT
);

CREATE INDEX IF NOT EXISTS idx_training_pferd ON trainingseinheit(pferd_id, datum);
"""


class Database:
    """Kapselt die SQLite-Verbindung und die Schemainitialisierung."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()
        self._seed_stammdaten()

    def _create_schema(self) -> None:
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def _seed_stammdaten(self) -> None:
        """Legt die Standard-Trainingsarten und -Schwerpunkte an."""
        cur = self.connection.cursor()
        for bezeichnung in STANDARD_TRAININGSARTEN:
            cur.execute(
                "INSERT OR IGNORE INTO trainingsart (bezeichnung) VALUES (?)",
                (bezeichnung,),
            )
        for bezeichnung in STANDARD_SCHWERPUNKTE:
            cur.execute(
                "INSERT OR IGNORE INTO schwerpunkt (bezeichnung) VALUES (?)",
                (bezeichnung,),
            )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
