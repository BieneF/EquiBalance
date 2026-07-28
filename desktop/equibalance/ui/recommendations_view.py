"""Ansicht: Empfehlungen (FA-13) – regelbasierte Hinweise."""

from __future__ import annotations

from tkinter import ttk

from ..config import COLORS
from .widgets import Card


PRIO_FARBE = {
    "hoch": COLORS["danger"],
    "mittel": COLORS["accent"],
    "niedrig": COLORS["primary"],
}


class EmpfehlungenView(ttk.Frame):
    """Zeigt die zur Laufzeit berechneten Trainingsempfehlungen (GR-07)."""

    titel = "Empfehlungen"

    def __init__(self, master, app) -> None:
        super().__init__(master, style="Content.TFrame")
        self.app = app

        self.info = ttk.Label(self, style="Muted.TLabel", wraplength=760, text="")
        self.info.pack(anchor="w", pady=(0, 12))

        container = Card(self)
        container.pack(fill="both", expand=True)

        leinwand = ttk.Frame(container, style="Card.TFrame")
        leinwand.pack(fill="both", expand=True)
        self.liste = leinwand

    def aktualisieren(self) -> None:
        for widget in self.liste.winfo_children():
            widget.destroy()

        pferd = self.app.aktuelles_pferd
        if pferd is None:
            self.info.configure(text="Kein Pferd ausgewählt.")
            return

        self.info.configure(
            text=(
                f"Die Hinweise werden auf Basis der Trainingsdaten von {pferd.name} "
                "berechnet und nicht dauerhaft gespeichert (GR-07). Grundlage sind die "
                "Geschäftsregeln GR-09 bis GR-13."
            )
        )

        for empfehlung in self.app.empfehlungen():
            block = ttk.Frame(self.liste, style="Card.TFrame")
            block.pack(fill="x", pady=(0, 14))

            kopf = ttk.Frame(block, style="Card.TFrame")
            kopf.pack(fill="x")
            marker = ttk.Label(
                kopf, text=f" {empfehlung.prioritaet.upper()} ",
                style="Badge.TLabel",
            )
            marker.pack(side="left")
            marker.configure(background=PRIO_FARBE.get(empfehlung.prioritaet,
                                                       COLORS["primary"]))
            ttk.Label(kopf, text=f"{empfehlung.kategorie} · Regel {empfehlung.regel}",
                      style="Muted.TLabel").pack(side="left", padx=8)

            ttk.Label(block, text=empfehlung.titel, style="HinweisTitel.TLabel",
                      wraplength=760).pack(anchor="w", pady=(6, 2))
            ttk.Label(block, text=empfehlung.text, style="Value.TLabel",
                      wraplength=760).pack(anchor="w")
            ttk.Separator(block, orient="horizontal").pack(fill="x", pady=(12, 0))
