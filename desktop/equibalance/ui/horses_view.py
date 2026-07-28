"""Ansicht: Pferdeverwaltung (FA-01 bis FA-03, FA-16)."""

from __future__ import annotations

from tkinter import messagebox, ttk

from ..models import Pferd
from ..widgets_helpers import format_minuten
from .dialogs import PferdDialog
from .widgets import Card
import tkinter as tk


class PferdeView(ttk.Frame):
    """Liste aller Pferde inklusive Steckbrief und Verwaltungsfunktionen."""

    titel = "Pferdeverwaltung"

    def __init__(self, master, app) -> None:
        super().__init__(master, style="Content.TFrame")
        self.app = app

        self.columnconfigure(0, weight=2, uniform="p")
        self.columnconfigure(1, weight=3, uniform="p")
        self.rowconfigure(0, weight=1)

        # -------------------------------------------------------- Liste links
        links = Card(self, "Pferde")
        links.grid(row=0, column=0, sticky="nsew")

        self.var_archiv = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            links, text="Archivierte Pferde anzeigen", variable=self.var_archiv,
            style="Switch.TCheckbutton", command=self.aktualisieren,
        ).pack(anchor="w", pady=(0, 8))

        self.liste = ttk.Treeview(
            links, columns=("name", "status"), show="headings", height=14
        )
        self.liste.heading("name", text="Name")
        self.liste.heading("status", text="Status")
        self.liste.column("name", width=160)
        self.liste.column("status", width=90)
        self.liste.pack(fill="both", expand=True)
        self.liste.bind("<<TreeviewSelect>>", self._auswahl_geaendert)

        knoepfe = ttk.Frame(links, style="Card.TFrame")
        knoepfe.pack(fill="x", pady=(12, 0))
        ttk.Button(knoepfe, text="Neues Pferd", style="Primary.TButton",
                   command=self.neu).pack(side="left")
        ttk.Button(knoepfe, text="Bearbeiten", style="Ghost.TButton",
                   command=self.bearbeiten).pack(side="left", padx=6)
        self.btn_archiv = ttk.Button(knoepfe, text="Archivieren", style="Ghost.TButton",
                                     command=self.archivieren)
        self.btn_archiv.pack(side="left")

        # ----------------------------------------------------- Steckbrief rechts
        rechts = Card(self, "Steckbrief")
        rechts.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        self.steckbrief = ttk.Frame(rechts, style="Card.TFrame")
        self.steckbrief.pack(fill="both", expand=True)

        self._pferde: list[Pferd] = []

    # ---------------------------------------------------------------- Aktionen
    def _gewaehltes_pferd(self) -> Pferd | None:
        auswahl = self.liste.selection()
        if not auswahl:
            return None
        index = self.liste.index(auswahl[0])
        return self._pferde[index] if index < len(self._pferde) else None

    def _auswahl_geaendert(self, _event=None) -> None:
        pferd = self._gewaehltes_pferd()
        if pferd:
            self.app.setze_aktuelles_pferd(pferd, benachrichtigen=True)
        self._zeichne_steckbrief(pferd)

    def neu(self) -> None:
        pferd = PferdDialog(self).zeige()
        if pferd:
            self.app.pferd_repo.anlegen(pferd)
            self.app.setze_aktuelles_pferd(pferd)
            self.app.alles_aktualisieren()

    def bearbeiten(self) -> None:
        pferd = self._gewaehltes_pferd()
        if not pferd:
            messagebox.showinfo("Kein Pferd gewählt",
                                "Bitte wählen Sie zuerst ein Pferd aus.")
            return
        geaendert = PferdDialog(self, pferd).zeige()
        if geaendert:
            self.app.pferd_repo.aktualisieren(geaendert)
            self.app.alles_aktualisieren()

    def archivieren(self) -> None:
        pferd = self._gewaehltes_pferd()
        if not pferd:
            messagebox.showinfo("Kein Pferd gewählt",
                                "Bitte wählen Sie zuerst ein Pferd aus.")
            return
        neuer_status = not pferd.archiviert
        aktion = "archivieren" if neuer_status else "reaktivieren"
        if not messagebox.askyesno("Bestätigung",
                                   f"Möchten Sie {pferd.name} wirklich {aktion}?"):
            return
        self.app.pferd_repo.archivieren(pferd.pferd_id, neuer_status)
        self.app.alles_aktualisieren()

    # ----------------------------------------------------------- Aktualisierung
    def aktualisieren(self) -> None:
        self._pferde = self.app.pferd_repo.liste(
            inklusive_archiviert=self.var_archiv.get()
        )
        self.liste.delete(*self.liste.get_children())
        aktuelles = self.app.aktuelles_pferd
        auswahl_id = None
        for pferd in self._pferde:
            item = self.liste.insert(
                "", "end",
                values=(pferd.name, "archiviert" if pferd.archiviert else "aktiv"),
            )
            if aktuelles and pferd.pferd_id == aktuelles.pferd_id:
                auswahl_id = item
        if auswahl_id:
            self.liste.selection_set(auswahl_id)
        self._zeichne_steckbrief(self._gewaehltes_pferd())

    def _zeichne_steckbrief(self, pferd: Pferd | None) -> None:
        for widget in self.steckbrief.winfo_children():
            widget.destroy()

        if pferd is None:
            ttk.Label(self.steckbrief, style="Muted.TLabel", wraplength=380,
                      text="Wählen Sie ein Pferd aus der Liste, um Details zu sehen."
                      ).pack(anchor="w")
            self.btn_archiv.configure(text="Archivieren")
            return

        self.btn_archiv.configure(
            text="Reaktivieren" if pferd.archiviert else "Archivieren"
        )
        ttk.Label(self.steckbrief, text=pferd.name, style="H2.TLabel").pack(anchor="w")

        einheiten = self.app.training_repo.liste_fuer_pferd(pferd.pferd_id)
        minuten = sum(e.dauer for e in einheiten)
        letztes = max((e.datum for e in einheiten), default=None)

        zeilen = [
            ("Geburtsjahr", str(pferd.geburtsjahr) if pferd.geburtsjahr else "–"),
            ("Alter", f"{pferd.alter} Jahre" if pferd.alter is not None else "–"),
            ("Rasse", pferd.rasse or "–"),
            ("Geschlecht", pferd.geschlecht or "–"),
            ("Status", "archiviert" if pferd.archiviert else "aktiv"),
            ("Trainingseinheiten", str(len(einheiten))),
            ("Trainingszeit gesamt", format_minuten(minuten)),
            ("Letztes Training",
             letztes.strftime("%d.%m.%Y") if letztes else "noch keins"),
        ]
        tabelle = ttk.Frame(self.steckbrief, style="Card.TFrame")
        tabelle.pack(fill="x", pady=(14, 0))
        for i, (label, wert) in enumerate(zeilen):
            ttk.Label(tabelle, text=label, style="FieldLabel.TLabel").grid(
                row=i, column=0, sticky="w", pady=3
            )
            ttk.Label(tabelle, text=wert, style="Value.TLabel").grid(
                row=i, column=1, sticky="w", padx=(24, 0), pady=3
            )
