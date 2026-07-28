"""Kleine Formatierungshelfer für die Oberfläche."""

from __future__ import annotations

from datetime import date


def format_datum(wert: date | None) -> str:
    return wert.strftime("%d.%m.%Y") if wert else "–"


def format_minuten(minuten: int) -> str:
    stunden, rest = divmod(int(minuten), 60)
    if stunden and rest:
        return f"{stunden} h {rest} min"
    if stunden:
        return f"{stunden} h"
    return f"{rest} min"
