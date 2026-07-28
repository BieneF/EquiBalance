"""Ansicht: Trainingsverwaltung (FA-04 bis FA-06, FA-08, FA-17)."""

from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk

from ..widgets_helpers import format_minuten
from .dialogs import TrainingDialog
from .widgets import Card

ZEITRAEUME = {
    "Letzte 7 Tage": 7,
    "Letzte 21 Tage": 21,
    "Letzte 30 Tage": 30,
    "Letzte 90 Tage": 90,
    "Gesamter Zeitraum": None,
}


class TrainingsView(ttk.Frame):
    """Tabellarische Verwaltung der Trainingseinheiten des gewählten Pferdes."""

    titel = "Trainingsverwaltung"

    def __init__(self, master, app) -> None:
        super().__init__(master, style="Content.TFrame")
        self.app = app

        kopf = ttk.Frame(self, style="Content.TFrame")
        kopf.pack(fill="x")

        ttk.Label(kopf, text="Zeitraum:", style="FieldLabel.TLabel").pack(side="left")
        self.var_zeitraum = tk.StringVar(value="Letzte 30 Tage")
        ttk.Combobox(kopf, textvariable=self.var_zeitraum, state="readonly", width=20,
                     values=list(ZEITRAEUME)).pack(side="left", padx=(8, 16))
        self.var_zeitraum.trace_add("write", lambda *_: self.aktualisieren())

        ttk.Button(kopf, text="Trainingseinheit erfassen", style="Primary.TButton",
                   command=self.neu).pack(side="right")
        ttk.Button(kopf, text="Löschen", style="Danger.TButton",
                   command=self.loeschen).pack(side="right", padx=6)
        ttk.Button(kopf, text="Bearbeiten", style="Ghost.TButton",
                   command=self.bearbeiten).pack(side="right")

        karte = Card(self)
        karte.pack(fill="both", expand=True, pady=(14, 0))

        self.summe = ttk.Label(karte, text="", style="Muted.TLabel")
        self.summe.pack(anchor="w", pady=(0, 8))

        spalten = ("datum", "art", "dauer", "intensitaet", "schwerpunkt", "ort",
                   "wetter", "notizen")
        self.tabelle = ttk.Treeview(karte, columns=spalten, show="headings")
        beschriftungen = {
            "datum": ("Datum", 90),
            "art": ("Trainingsart", 110),
            "dauer": ("Dauer", 70),
            "intensitaet": ("Intensität", 90),
            "schwerpunkt": ("Schwerpunkt", 120),
            "ort": ("Ort", 110),
            "wetter": ("Wetter", 100),
            "notizen": ("Notizen", 220),
        }
        for spalte, (text, breite) in beschriftungen.items():
            self.tabelle.heading(spalte, text=text)
            self.tabelle.column(spalte, width=breite, anchor="w")

        scroll = ttk.Scrollbar(karte, orient="vertical", command=self.tabelle.yview)
        self.tabelle.configure(yscrollcommand=scroll.set)
        self.tabelle.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tabelle.bind("<Double-1>", lambda _e: self.bearbeiten())

        self._einheiten: list = []

    # ---------------------------------------------------------------- Aktionen
    def _gewaehlte_einheit(self):
        auswahl = self.tabelle.selection()
        if not auswahl:
            return None
        index = self.tabelle.index(auswahl[0])
        return self._einheiten[index] if index < len(self._einheiten) else None

    def neu(self) -> None:
        pferd = self.app.aktuelles_pferd
        if pferd is None:
            messagebox.showinfo("Kein Pferd gewählt",
                                "Bitte wählen Sie zuerst ein Pferd aus.")
            return
        if pferd.archiviert:
            messagebox.showwarning(
                "Pferd archiviert",
                "Archivierte Pferde dürfen keine neuen Trainingseinheiten erhalten "
                "(Geschäftsregel GR-06).",
            )
            return
        einheit = TrainingDialog(
            self, pferd, self.app.trainingsarten, self.app.schwerpunkte
        ).zeige()
        if einheit:
            self.app.training_repo.anlegen(einheit)
            self.app.alles_aktualisieren()

    def bearbeiten(self) -> None:
        einheit = self._gewaehlte_einheit()
        if not einheit:
            messagebox.showinfo("Keine Auswahl",
                                "Bitte wählen Sie zuerst eine Trainingseinheit aus.")
            return
        geaendert = TrainingDialog(
            self, self.app.aktuelles_pferd, self.app.trainingsarten,
            self.app.schwerpunkte, einheit,
        ).zeige()
        if geaendert:
            self.app.training_repo.aktualisieren(geaendert)
            self.app.alles_aktualisieren()

    def loeschen(self) -> None:
        einheit = self._gewaehlte_einheit()
        if not einheit:
            messagebox.showinfo("Keine Auswahl",
                                "Bitte wählen Sie zuerst eine Trainingseinheit aus.")
            return
        if not messagebox.askyesno(
            "Trainingseinheit löschen",
            f"Soll die Einheit vom {einheit.datum.strftime('%d.%m.%Y')} "
            "wirklich gelöscht werden?",
        ):
            return
        self.app.training_repo.loeschen(einheit.training_id)
        self.app.alles_aktualisieren()

    # ----------------------------------------------------------- Aktualisierung
    def aktualisieren(self) -> None:
        self.tabelle.delete(*self.tabelle.get_children())
        self._einheiten = []
        pferd = self.app.aktuelles_pferd
        if pferd is None:
            self.summe.configure(text="Kein Pferd ausgewählt.")
            return

        tage = ZEITRAEUME.get(self.var_zeitraum.get())
        von = date.today() - timedelta(days=tage - 1) if tage else None
        self._einheiten = self.app.training_repo.liste_fuer_pferd(
            pferd.pferd_id, von=von
        )

        for e in self._einheiten:
            self.tabelle.insert(
                "", "end",
                values=(
                    e.datum.strftime("%d.%m.%Y"), e.trainingsart, f"{e.dauer} min",
                    e.intensitaet, e.schwerpunkt, e.trainingsort or "–",
                    e.wetter or "–", (e.notizen or "").replace("\n", " ")[:80],
                ),
            )

        minuten = sum(e.dauer for e in self._einheiten)
        self.summe.configure(
            text=f"{pferd.name} · {len(self._einheiten)} Einheiten · "
                 f"{format_minuten(minuten)} Gesamtdauer"
        )
