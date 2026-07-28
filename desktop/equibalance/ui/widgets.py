"""Wiederverwendbare Oberflächenbausteine und Diagramme (reines Tkinter)."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Dict, List

from ..config import CHART_COLORS, COLORS


class Card(ttk.Frame):
    """Weiße Inhaltskarte mit Überschrift."""

    def __init__(self, master, titel: str = "", **kwargs) -> None:
        super().__init__(master, style="Card.TFrame", padding=16, **kwargs)
        if titel:
            ttk.Label(self, text=titel, style="CardTitle.TLabel").pack(
                anchor="w", pady=(0, 10)
            )


class KennzahlCard(ttk.Frame):
    """Kachel für eine einzelne statistische Kennzahl."""

    def __init__(self, master, titel: str, wert: str = "–", einheit: str = "") -> None:
        super().__init__(master, style="Card.TFrame", padding=14)
        ttk.Label(self, text=titel.upper(), style="Kpi.TLabel").pack(anchor="w")
        zeile = ttk.Frame(self, style="Card.TFrame")
        zeile.pack(anchor="w", pady=(6, 0))
        self._wert = ttk.Label(zeile, text=wert, style="KpiValue.TLabel")
        self._wert.pack(side="left")
        self._einheit = ttk.Label(zeile, text=f" {einheit}", style="KpiUnit.TLabel")
        self._einheit.pack(side="left", anchor="s", pady=(0, 4))

    def setze(self, wert: str, einheit: str | None = None) -> None:
        self._wert.configure(text=wert)
        if einheit is not None:
            self._einheit.configure(text=f" {einheit}")


class ChartCanvas(tk.Canvas):
    """Basisklasse für die selbst gezeichneten Diagramme."""

    def __init__(self, master, height: int = 220, **kwargs) -> None:
        super().__init__(
            master,
            height=height,
            bg=COLORS["surface"],
            highlightthickness=0,
            **kwargs,
        )
        self._daten: Dict[str, float] = {}
        self.bind("<Configure>", lambda _e: self.zeichne())

    def setze_daten(self, daten: Dict[str, float]) -> None:
        self._daten = daten
        self.zeichne()

    def zeichne(self) -> None:  # pragma: no cover - Zeichenlogik
        raise NotImplementedError

    def _leer_hinweis(self, text: str = "Keine Daten im gewählten Zeitraum") -> None:
        self.create_text(
            self.winfo_width() / 2,
            self.winfo_height() / 2,
            text=text,
            fill=COLORS["muted"],
            font=("Segoe UI", 10),
        )


class BalkenDiagramm(ChartCanvas):
    """Horizontales Balkendiagramm, z. B. für die Verteilung der Trainingsarten."""

    def __init__(self, master, einheit: str = "", **kwargs) -> None:
        self.einheit = einheit
        super().__init__(master, **kwargs)

    def zeichne(self) -> None:
        self.delete("all")
        breite, hoehe = self.winfo_width(), self.winfo_height()
        if breite < 50 or hoehe < 40:
            return
        if not self._daten or sum(self._daten.values()) == 0:
            self._leer_hinweis()
            return

        eintraege = list(self._daten.items())
        label_breite = 120
        max_wert = max(self._daten.values())
        zeilen_hoehe = min(34, max(18, (hoehe - 10) / len(eintraege)))
        y = 8

        for i, (label, wert) in enumerate(eintraege):
            farbe = CHART_COLORS[i % len(CHART_COLORS)]
            balken_max = breite - label_breite - 60
            laenge = max(2, (wert / max_wert) * balken_max)
            mitte = y + zeilen_hoehe / 2
            self.create_text(
                label_breite - 10, mitte, text=label, anchor="e",
                fill=COLORS["text"], font=("Segoe UI", 9),
            )
            self.create_rectangle(
                label_breite, y + 4, label_breite + laenge, y + zeilen_hoehe - 4,
                fill=farbe, outline="",
            )
            self.create_text(
                label_breite + laenge + 8, mitte,
                text=f"{wert:g} {self.einheit}".strip(), anchor="w",
                fill=COLORS["muted"], font=("Segoe UI", 9),
            )
            y += zeilen_hoehe


class SaeulenDiagramm(ChartCanvas):
    """Vertikales Säulendiagramm, z. B. Trainingsminuten pro Woche."""

    def __init__(self, master, einheit: str = "min", **kwargs) -> None:
        self.einheit = einheit
        super().__init__(master, **kwargs)

    def zeichne(self) -> None:
        self.delete("all")
        breite, hoehe = self.winfo_width(), self.winfo_height()
        if breite < 50 or hoehe < 40:
            return
        if not self._daten:
            self._leer_hinweis()
            return

        eintraege = list(self._daten.items())
        max_wert = max(self._daten.values()) or 1
        rand_unten, rand_oben = 26, 18
        plot_hoehe = hoehe - rand_unten - rand_oben
        spalte = breite / len(eintraege)
        balken_breite = min(38, spalte * 0.55)

        self.create_line(
            0, hoehe - rand_unten, breite, hoehe - rand_unten,
            fill=COLORS["border"],
        )

        for i, (label, wert) in enumerate(eintraege):
            x = spalte * i + spalte / 2
            h = (wert / max_wert) * plot_hoehe
            self.create_rectangle(
                x - balken_breite / 2, hoehe - rand_unten - h,
                x + balken_breite / 2, hoehe - rand_unten,
                fill=COLORS["primary"], outline="",
            )
            if wert:
                self.create_text(
                    x, hoehe - rand_unten - h - 9, text=f"{wert:g}",
                    fill=COLORS["muted"], font=("Segoe UI", 8),
                )
            self.create_text(
                x, hoehe - rand_unten + 12, text=label,
                fill=COLORS["muted"], font=("Segoe UI", 8),
            )


class RingDiagramm(ChartCanvas):
    """Ringdiagramm mit Legende, z. B. Verteilung der Schwerpunkte."""

    def zeichne(self) -> None:
        self.delete("all")
        breite, hoehe = self.winfo_width(), self.winfo_height()
        if breite < 60 or hoehe < 60:
            return
        gesamt = sum(self._daten.values())
        if not self._daten or gesamt == 0:
            self._leer_hinweis()
            return

        durchmesser = min(hoehe - 20, breite / 2 - 20)
        x0, y0 = 16, (hoehe - durchmesser) / 2
        x1, y1 = x0 + durchmesser, y0 + durchmesser
        start = 90.0

        for i, (label, wert) in enumerate(self._daten.items()):
            winkel = wert / gesamt * 360
            self.create_arc(
                x0, y0, x1, y1, start=start, extent=-winkel,
                fill=CHART_COLORS[i % len(CHART_COLORS)], outline=COLORS["surface"],
                width=2,
            )
            start -= winkel

        loch = durchmesser * 0.5
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        self.create_oval(
            cx - loch / 2, cy - loch / 2, cx + loch / 2, cy + loch / 2,
            fill=COLORS["surface"], outline="",
        )
        self.create_text(
            cx, cy, text=f"{gesamt:g}", fill=COLORS["text"],
            font=("Segoe UI", 13, "bold"),
        )

        ly = 18
        for i, (label, wert) in enumerate(self._daten.items()):
            lx = x1 + 30
            self.create_rectangle(
                lx, ly, lx + 11, ly + 11,
                fill=CHART_COLORS[i % len(CHART_COLORS)], outline="",
            )
            self.create_text(
                lx + 18, ly + 5,
                text=f"{label}  ({wert / gesamt * 100:.0f} %)",
                anchor="w", fill=COLORS["text"], font=("Segoe UI", 9),
            )
            ly += 20


class IndexAnzeige(ChartCanvas):
    """Tachometer-Darstellung des Ausgewogenheitsindex (0-100)."""

    def __init__(self, master, **kwargs) -> None:
        self._wert = 0.0
        super().__init__(master, **kwargs)

    def setze_wert(self, wert: float) -> None:
        self._wert = max(0.0, min(100.0, wert))
        self.zeichne()

    def zeichne(self) -> None:
        self.delete("all")
        breite, hoehe = self.winfo_width(), self.winfo_height()
        if breite < 60 or hoehe < 60:
            return
        groesse = min(breite - 30, (hoehe - 30) * 2)
        x0 = (breite - groesse) / 2
        y0 = (hoehe - groesse / 2) / 2 - 6
        self.create_arc(
            x0, y0, x0 + groesse, y0 + groesse, start=0, extent=180,
            style="arc", outline=COLORS["border"], width=16,
        )
        self.create_arc(
            x0, y0, x0 + groesse, y0 + groesse, start=180,
            extent=-(self._wert / 100 * 180), style="arc",
            outline=COLORS["primary"], width=16,
        )
        self.create_text(
            x0 + groesse / 2, y0 + groesse / 2 - 12,
            text=f"{self._wert:.0f}", fill=COLORS["text"],
            font=("Segoe UI", 22, "bold"),
        )
        self.create_text(
            x0 + groesse / 2, y0 + groesse / 2 + 12,
            text="Ausgewogenheitsindex", fill=COLORS["muted"],
            font=("Segoe UI", 9),
        )


class Kalenderansicht(ChartCanvas):
    """Heatmap-Kalender der Trainingstage (letzte 12 Wochen)."""

    def __init__(self, master, **kwargs) -> None:
        self._tage: Dict[str, int] = {}
        self._spalten = 12
        super().__init__(master, height=140, **kwargs)

    def setze_tage(self, tage_minuten: Dict[str, int], spalten: int = 12) -> None:
        self._tage = tage_minuten
        self._spalten = spalten
        self.zeichne()

    def zeichne(self) -> None:
        self.delete("all")
        breite, hoehe = self.winfo_width(), self.winfo_height()
        if breite < 60 or hoehe < 40 or not self._tage:
            if breite > 60:
                self._leer_hinweis("Noch keine Trainingstage erfasst")
            return

        werte = list(self._tage.values())
        max_wert = max(werte) or 1
        zelle = min(16, (breite - 40) / self._spalten - 3)
        abstand = 3
        x_start = 34

        for idx, (tag, minuten) in enumerate(self._tage.items()):
            spalte, zeile = divmod(idx, 7)
            x = x_start + spalte * (zelle + abstand)
            y = 14 + zeile * (zelle + abstand)
            if minuten == 0:
                farbe = "#e8e4dc"
            else:
                anteil = minuten / max_wert
                farbe = self._farbstufe(anteil)
            self.create_rectangle(
                x, y, x + zelle, y + zelle, fill=farbe, outline="",
            )

        for i, name in enumerate(["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]):
            self.create_text(
                26, 14 + i * (zelle + abstand) + zelle / 2, text=name, anchor="e",
                fill=COLORS["muted"], font=("Segoe UI", 8),
            )

    @staticmethod
    def _farbstufe(anteil: float) -> str:
        stufen = ["#c8d8c6", "#a3bfa1", "#7ea27d", "#5b7f5e"]
        index = min(len(stufen) - 1, int(math.ceil(anteil * len(stufen)) - 1))
        return stufen[max(0, index)]


def leere_liste_hinweis(master, text: str) -> ttk.Label:
    return ttk.Label(master, text=text, style="Muted.TLabel", wraplength=520)
