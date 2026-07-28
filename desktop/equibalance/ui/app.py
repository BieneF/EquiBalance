"""Hauptfenster der Anwendung EquiBalance (Navigation und Steuerung)."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk
from typing import List, Optional

from ..config import APP_NAME, APP_VERSION, COLORS, DB_PATH
from ..data import (
    Database,
    PferdRepository,
    StammdatenRepository,
    TrainingRepository,
)
from ..models import Pferd
from ..services import AnalyseService, EmpfehlungsService
from .analysis_view import AnalyseView
from .dashboard_view import DashboardView
from .horses_view import PferdeView
from .recommendations_view import EmpfehlungenView
from .trainings_view import TrainingsView


class EquiBalanceApp(tk.Tk):
    """Fasst Datenzugriff, Fachlogik und Oberfläche zusammen."""

    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} – Trainingsmanagement für Pferde")
        self.geometry("1240x800")
        self.minsize(1080, 720)
        self.configure(bg=COLORS["bg"])

        # ---------------------------------------------------------- Datenschicht
        self.database = Database()
        self.pferd_repo = PferdRepository(self.database.connection)
        self.training_repo = TrainingRepository(self.database.connection)
        self.stammdaten_repo = StammdatenRepository(self.database.connection)

        # ------------------------------------------------------------- Fachlogik
        self.analyse_service = AnalyseService()
        self.empfehlungs_service = EmpfehlungsService()

        self.trainingsarten = self.stammdaten_repo.trainingsarten()
        self.schwerpunkte = self.stammdaten_repo.schwerpunkte()
        self.aktuelles_pferd: Optional[Pferd] = None

        self._styles()
        self._layout()

        pferde = self.pferd_repo.liste()
        if pferde:
            self.aktuelles_pferd = pferde[0]
        self.alles_aktualisieren()
        self.zeige_ansicht("Dashboard")

        self.protocol("WM_DELETE_WINDOW", self._beenden)

    # ------------------------------------------------------------------ Styling
    def _styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        basis = "Segoe UI" if "Segoe UI" in tkfont.families() else "Helvetica"

        style.configure(".", font=(basis, 10), background=COLORS["bg"],
                        foreground=COLORS["text"])
        style.configure("Content.TFrame", background=COLORS["bg"])
        style.configure("Dialog.TFrame", background=COLORS["bg"])
        style.configure("Card.TFrame", background=COLORS["surface"],
                        relief="flat", borderwidth=0)
        style.configure("Sidebar.TFrame", background=COLORS["sidebar"])
        style.configure("Header.TFrame", background=COLORS["bg"])

        style.configure("CardTitle.TLabel", background=COLORS["surface"],
                        foreground=COLORS["text"], font=(basis, 11, "bold"))
        style.configure("H1.TLabel", background=COLORS["bg"],
                        foreground=COLORS["text"], font=(basis, 19, "bold"))
        style.configure("H2.TLabel", background=COLORS["surface"],
                        foreground=COLORS["text"], font=(basis, 14, "bold"))
        style.configure("Muted.TLabel", background=COLORS["surface"],
                        foreground=COLORS["muted"], font=(basis, 9))
        style.configure("Value.TLabel", background=COLORS["surface"],
                        foreground=COLORS["text"], font=(basis, 10))
        style.configure("FieldLabel.TLabel", background=COLORS["bg"],
                        foreground=COLORS["muted"], font=(basis, 9, "bold"))
        style.configure("DialogTitle.TLabel", background=COLORS["bg"],
                        foreground=COLORS["text"], font=(basis, 14, "bold"))
        style.configure("Kpi.TLabel", background=COLORS["surface"],
                        foreground=COLORS["muted"], font=(basis, 8, "bold"))
        style.configure("KpiValue.TLabel", background=COLORS["surface"],
                        foreground=COLORS["text"], font=(basis, 22, "bold"))
        style.configure("KpiUnit.TLabel", background=COLORS["surface"],
                        foreground=COLORS["muted"], font=(basis, 9))
        style.configure("HinweisTitel.TLabel", background=COLORS["surface"],
                        foreground=COLORS["text"], font=(basis, 10, "bold"))
        style.configure("Badge.TLabel", background=COLORS["primary"],
                        foreground="#ffffff", font=(basis, 8, "bold"))
        style.configure("SidebarTitle.TLabel", background=COLORS["sidebar"],
                        foreground=COLORS["sidebar_fg"], font=(basis, 15, "bold"))
        style.configure("SidebarSub.TLabel", background=COLORS["sidebar"],
                        foreground="#b9c9b7", font=(basis, 8))

        style.configure("Primary.TButton", background=COLORS["primary"],
                        foreground="#ffffff", borderwidth=0, padding=(14, 7),
                        font=(basis, 10, "bold"))
        style.map("Primary.TButton",
                  background=[("active", COLORS["sidebar_active"])])
        style.configure("Ghost.TButton", background=COLORS["bg"],
                        foreground=COLORS["text"], borderwidth=1, padding=(12, 6))
        style.map("Ghost.TButton", background=[("active", "#e7e2d8")])
        style.configure("Danger.TButton", background=COLORS["danger"],
                        foreground="#ffffff", borderwidth=0, padding=(12, 6))
        style.map("Danger.TButton", background=[("active", "#8b342e")])
        style.configure("Nav.TButton", background=COLORS["sidebar"],
                        foreground=COLORS["sidebar_fg"], borderwidth=0,
                        anchor="w", padding=(16, 11), font=(basis, 10))
        style.map("Nav.TButton",
                  background=[("active", COLORS["sidebar_active"])])
        style.configure("NavActive.TButton", background=COLORS["sidebar_active"],
                        foreground="#ffffff", borderwidth=0, anchor="w",
                        padding=(16, 11), font=(basis, 10, "bold"))
        style.map("NavActive.TButton",
                  background=[("active", COLORS["sidebar_active"])])

        style.configure("Switch.TCheckbutton", background=COLORS["surface"],
                        foreground=COLORS["text"])
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff",
                        foreground=COLORS["text"], rowheight=26, borderwidth=0)
        style.configure("Treeview.Heading", background="#efeae1",
                        foreground=COLORS["muted"], font=(basis, 9, "bold"),
                        borderwidth=0)
        style.map("Treeview", background=[("selected", COLORS["primary"])],
                  foreground=[("selected", "#ffffff")])

    # ------------------------------------------------------------------- Layout
    def _layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Navigationsleiste
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=216)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        kopf = ttk.Frame(sidebar, style="Sidebar.TFrame")
        kopf.pack(fill="x", pady=(24, 26), padx=18)
        ttk.Label(kopf, text="EquiBalance", style="SidebarTitle.TLabel").pack(anchor="w")
        ttk.Label(kopf, text="Trainingsmanagement", style="SidebarSub.TLabel").pack(
            anchor="w"
        )

        self.nav_buttons: dict[str, ttk.Button] = {}
        for name in ["Dashboard", "Pferdeverwaltung", "Trainingsverwaltung",
                     "Analyse", "Empfehlungen"]:
            btn = ttk.Button(sidebar, text=name, style="Nav.TButton",
                             command=lambda n=name: self.zeige_ansicht(n))
            btn.pack(fill="x")
            self.nav_buttons[name] = btn

        fuss = ttk.Frame(sidebar, style="Sidebar.TFrame")
        fuss.pack(side="bottom", fill="x", padx=18, pady=16)
        ttk.Label(fuss, text=f"Version {APP_VERSION}", style="SidebarSub.TLabel").pack(
            anchor="w"
        )
        ttk.Label(fuss, text="lokal · offline", style="SidebarSub.TLabel").pack(
            anchor="w"
        )

        # Hauptbereich
        haupt = ttk.Frame(self, style="Content.TFrame", padding=(24, 20))
        haupt.grid(row=0, column=1, sticky="nsew")
        haupt.columnconfigure(0, weight=1)
        haupt.rowconfigure(1, weight=1)

        header = ttk.Frame(haupt, style="Header.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self.titel_label = ttk.Label(header, text="Dashboard", style="H1.TLabel")
        self.titel_label.pack(side="left")

        auswahl = ttk.Frame(header, style="Header.TFrame")
        auswahl.pack(side="right")
        ttk.Label(auswahl, text="Aktives Pferd", style="FieldLabel.TLabel").pack(
            side="left", padx=(0, 8)
        )
        self.var_pferd = tk.StringVar()
        self.combo_pferd = ttk.Combobox(auswahl, textvariable=self.var_pferd,
                                        state="readonly", width=24)
        self.combo_pferd.pack(side="left")
        self.combo_pferd.bind("<<ComboboxSelected>>", self._pferd_gewechselt)

        self.container = ttk.Frame(haupt, style="Content.TFrame")
        self.container.grid(row=1, column=0, sticky="nsew")
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)

        self.views = {
            "Dashboard": DashboardView(self.container, self),
            "Pferdeverwaltung": PferdeView(self.container, self),
            "Trainingsverwaltung": TrainingsView(self.container, self),
            "Analyse": AnalyseView(self.container, self),
            "Empfehlungen": EmpfehlungenView(self.container, self),
        }
        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

        self.aktive_ansicht = "Dashboard"

    # --------------------------------------------------------------- Steuerung
    def zeige_ansicht(self, name: str) -> None:
        self.aktive_ansicht = name
        self.titel_label.configure(text=name)
        for key, btn in self.nav_buttons.items():
            btn.configure(style="NavActive.TButton" if key == name else "Nav.TButton")
        view = self.views[name]
        view.aktualisieren()
        view.tkraise()

    def setze_aktuelles_pferd(self, pferd: Pferd, benachrichtigen: bool = False) -> None:
        self.aktuelles_pferd = pferd
        self.var_pferd.set(pferd.name if pferd else "")
        if benachrichtigen:
            for name, view in self.views.items():
                if name != self.aktive_ansicht:
                    continue
                view.aktualisieren()

    def _pferd_gewechselt(self, _event=None) -> None:
        name = self.var_pferd.get()
        pferd = next((p for p in self._pferdeliste if p.name == name), None)
        if pferd:
            self.aktuelles_pferd = pferd
            self.alles_aktualisieren(pferdliste_neu_laden=False)

    def alles_aktualisieren(self, pferdliste_neu_laden: bool = True) -> None:
        """Aktualisiert Pferdauswahl und alle Ansichten (Dialogfluss)."""
        if pferdliste_neu_laden:
            self._pferdeliste = self.pferd_repo.liste(inklusive_archiviert=True)
            self.combo_pferd.configure(values=[p.name for p in self._pferdeliste])
            if self.aktuelles_pferd:
                aktualisiert = self.pferd_repo.lade(self.aktuelles_pferd.pferd_id)
                self.aktuelles_pferd = aktualisiert
            if self.aktuelles_pferd is None and self._pferdeliste:
                self.aktuelles_pferd = self._pferdeliste[0]
            self.var_pferd.set(
                self.aktuelles_pferd.name if self.aktuelles_pferd else ""
            )
        for view in self.views.values():
            view.aktualisieren()

    # ----------------------------------------------------------- Fachfunktionen
    def trainingseinheiten(self) -> List:
        if not self.aktuelles_pferd:
            return []
        return self.training_repo.liste_fuer_pferd(self.aktuelles_pferd.pferd_id)

    def analyse(self):
        return self.analyse_service.analysiere(
            self.trainingseinheiten(),
            [a.bezeichnung for a in self.trainingsarten],
        )

    def empfehlungen(self):
        return self.empfehlungs_service.erzeuge(
            self.trainingseinheiten(),
            [a.bezeichnung for a in self.trainingsarten],
            [s.bezeichnung for s in self.schwerpunkte],
        )

    # --------------------------------------------------------------- Beenden
    def _beenden(self) -> None:
        self.database.close()
        self.destroy()


def starte_anwendung() -> None:
    app = EquiBalanceApp()
    app.mainloop()
