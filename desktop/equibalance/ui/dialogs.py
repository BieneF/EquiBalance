"""Dialoge zur Erfassung und Bearbeitung von Pferden und Trainingseinheiten."""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk
from typing import List, Optional

from ..config import COLORS, GESCHLECHTER, INTENSITAETEN
from ..models import Pferd, Schwerpunkt, Trainingsart, Trainingseinheit
from ..services import ValidierungsFehler, validiere_pferd, validiere_trainingseinheit


class BasisDialog(tk.Toplevel):
    """Gemeinsame Grundfunktionen aller modalen Dialoge."""

    def __init__(self, master, titel: str, breite: int = 460, hoehe: int = 420) -> None:
        super().__init__(master)
        self.title(titel)
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.ergebnis = None

        self.body = ttk.Frame(self, style="Dialog.TFrame", padding=20)
        self.body.pack(fill="both", expand=True)

        ttk.Label(self.body, text=titel, style="DialogTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 14)
        )
        self.zeile = 1

        self.update_idletasks()
        x = master.winfo_toplevel().winfo_rootx() + 140
        y = master.winfo_toplevel().winfo_rooty() + 80
        self.geometry(f"{breite}x{hoehe}+{x}+{y}")

    def feld(self, label: str, widget: tk.Widget) -> tk.Widget:
        ttk.Label(self.body, text=label, style="FieldLabel.TLabel").grid(
            row=self.zeile, column=0, sticky="w", pady=(0, 2)
        )
        widget.grid(row=self.zeile + 1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.body.columnconfigure(0, weight=1)
        self.zeile += 2
        return widget

    def buttonleiste(self, speichern_text: str = "Speichern") -> None:
        leiste = ttk.Frame(self.body, style="Dialog.TFrame")
        leiste.grid(row=self.zeile, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(leiste, text="Abbrechen", style="Ghost.TButton",
                   command=self.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(leiste, text=speichern_text, style="Primary.TButton",
                   command=self.speichern).pack(side="left")

    def speichern(self) -> None:  # pragma: no cover - von Unterklassen überschrieben
        raise NotImplementedError

    def zeige(self):
        self.grab_set()
        self.wait_window()
        return self.ergebnis


class PferdDialog(BasisDialog):
    """Dialog zum Anlegen und Bearbeiten eines Pferdes (FA-01, FA-02)."""

    def __init__(self, master, pferd: Optional[Pferd] = None) -> None:
        bearbeiten = pferd is not None
        super().__init__(
            master,
            "Pferd bearbeiten" if bearbeiten else "Neues Pferd anlegen",
            hoehe=390,
        )
        self.pferd = pferd or Pferd()

        self.var_name = tk.StringVar(value=self.pferd.name)
        self.var_jahr = tk.StringVar(
            value=str(self.pferd.geburtsjahr) if self.pferd.geburtsjahr else ""
        )
        self.var_rasse = tk.StringVar(value=self.pferd.rasse)
        self.var_geschlecht = tk.StringVar(value=self.pferd.geschlecht or GESCHLECHTER[0])

        self.feld("Name *", ttk.Entry(self.body, textvariable=self.var_name))
        self.feld("Geburtsjahr", ttk.Entry(self.body, textvariable=self.var_jahr))
        self.feld("Rasse", ttk.Entry(self.body, textvariable=self.var_rasse))
        self.feld(
            "Geschlecht",
            ttk.Combobox(self.body, textvariable=self.var_geschlecht,
                         values=GESCHLECHTER, state="readonly"),
        )
        self.buttonleiste()

    def speichern(self) -> None:
        jahr_text = self.var_jahr.get().strip()
        if jahr_text and not jahr_text.isdigit():
            messagebox.showerror(
                "Ungültige Eingabe",
                "Das Geburtsjahr muss eine vierstellige Zahl sein.",
                parent=self,
            )
            return

        self.pferd.name = self.var_name.get().strip()
        self.pferd.geburtsjahr = int(jahr_text) if jahr_text else None
        self.pferd.rasse = self.var_rasse.get().strip()
        self.pferd.geschlecht = self.var_geschlecht.get()

        try:
            validiere_pferd(self.pferd)
        except ValidierungsFehler as fehler:
            messagebox.showerror("Eingabe unvollständig", str(fehler), parent=self)
            return

        self.ergebnis = self.pferd
        self.destroy()


class TrainingDialog(BasisDialog):
    """Dialog zum Erfassen und Bearbeiten einer Trainingseinheit (FA-04, FA-05)."""

    def __init__(
        self,
        master,
        pferd: Pferd,
        trainingsarten: List[Trainingsart],
        schwerpunkte: List[Schwerpunkt],
        einheit: Optional[Trainingseinheit] = None,
    ) -> None:
        bearbeiten = einheit is not None
        super().__init__(
            master,
            "Trainingseinheit bearbeiten" if bearbeiten else "Trainingseinheit erfassen",
            breite=500,
            hoehe=680,
        )
        self.pferd = pferd
        self.trainingsarten = trainingsarten
        self.schwerpunkte = schwerpunkte
        self.einheit = einheit or Trainingseinheit(
            pferd_id=pferd.pferd_id, datum=date.today(), intensitaet="mittel"
        )

        art_map = {a.trainingsart_id: a.bezeichnung for a in trainingsarten}
        sp_map = {s.schwerpunkt_id: s.bezeichnung for s in schwerpunkte}

        self.var_datum = tk.StringVar(
            value=(self.einheit.datum or date.today()).strftime("%d.%m.%Y")
        )
        self.var_art = tk.StringVar(
            value=art_map.get(self.einheit.trainingsart_id, trainingsarten[0].bezeichnung)
        )
        self.var_dauer = tk.StringVar(
            value=str(self.einheit.dauer) if self.einheit.dauer else "45"
        )
        self.var_intensitaet = tk.StringVar(value=self.einheit.intensitaet or "mittel")
        self.var_schwerpunkt = tk.StringVar(
            value=sp_map.get(self.einheit.schwerpunkt_id, schwerpunkte[0].bezeichnung)
        )
        self.var_ort = tk.StringVar(value=self.einheit.trainingsort)
        self.var_wetter = tk.StringVar(value=self.einheit.wetter)

        ttk.Label(self.body, text=f"Pferd: {pferd.name}", style="Muted.TLabel").grid(
            row=self.zeile, column=0, sticky="w", pady=(0, 10)
        )
        self.zeile += 1

        datum_zeile = ttk.Frame(self.body, style="Dialog.TFrame")
        ttk.Entry(datum_zeile, textvariable=self.var_datum, width=16).pack(side="left")
        ttk.Button(datum_zeile, text="Heute", style="Ghost.TButton",
                   command=lambda: self.var_datum.set(date.today().strftime("%d.%m.%Y"))
                   ).pack(side="left", padx=6)
        ttk.Button(datum_zeile, text="Kalender …", style="Ghost.TButton",
                   command=self._kalender_oeffnen).pack(side="left")
        self.feld("Datum * (TT.MM.JJJJ)", datum_zeile)

        self.feld(
            "Trainingsart *",
            ttk.Combobox(self.body, textvariable=self.var_art, state="readonly",
                         values=[a.bezeichnung for a in trainingsarten]),
        )
        self.feld("Dauer in Minuten *", ttk.Entry(self.body, textvariable=self.var_dauer))
        self.feld(
            "Intensität *",
            ttk.Combobox(self.body, textvariable=self.var_intensitaet,
                         state="readonly", values=INTENSITAETEN),
        )
        self.feld(
            "Schwerpunkt *",
            ttk.Combobox(self.body, textvariable=self.var_schwerpunkt,
                         state="readonly", values=[s.bezeichnung for s in schwerpunkte]),
        )
        self.feld("Trainingsort", ttk.Entry(self.body, textvariable=self.var_ort))
        self.feld("Wetter", ttk.Entry(self.body, textvariable=self.var_wetter))

        self.notizen = tk.Text(self.body, height=4, wrap="word",
                               relief="flat", bg="white", font=("Segoe UI", 10))
        self.notizen.insert("1.0", self.einheit.notizen)
        self.feld("Notizen", self.notizen)

        self.buttonleiste()

    # ------------------------------------------------------------- Kalender
    def _kalender_oeffnen(self) -> None:
        dialog = DatumsDialog(self, self._geparstes_datum() or date.today())
        gewaehlt = dialog.zeige()
        if gewaehlt:
            self.var_datum.set(gewaehlt.strftime("%d.%m.%Y"))

    def _geparstes_datum(self) -> Optional[date]:
        text = self.var_datum.get().strip()
        for muster in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                from datetime import datetime
                return datetime.strptime(text, muster).date()
            except ValueError:
                continue
        return None

    def speichern(self) -> None:
        datum = self._geparstes_datum()
        if datum is None:
            messagebox.showerror(
                "Ungültiges Datum",
                "Bitte geben Sie das Datum im Format TT.MM.JJJJ an.",
                parent=self,
            )
            return

        dauer_text = self.var_dauer.get().strip()
        dauer = int(dauer_text) if dauer_text.isdigit() else 0

        art = next((a for a in self.trainingsarten
                    if a.bezeichnung == self.var_art.get()), None)
        schwerpunkt = next((s for s in self.schwerpunkte
                            if s.bezeichnung == self.var_schwerpunkt.get()), None)

        self.einheit.pferd_id = self.pferd.pferd_id
        self.einheit.datum = datum
        self.einheit.dauer = dauer
        self.einheit.intensitaet = self.var_intensitaet.get()
        self.einheit.trainingsart_id = art.trainingsart_id if art else None
        self.einheit.schwerpunkt_id = schwerpunkt.schwerpunkt_id if schwerpunkt else None
        self.einheit.trainingsort = self.var_ort.get().strip()
        self.einheit.wetter = self.var_wetter.get().strip()
        self.einheit.notizen = self.notizen.get("1.0", "end").strip()

        try:
            validiere_trainingseinheit(self.einheit, self.pferd)
        except ValidierungsFehler as fehler:
            messagebox.showerror("Eingabe ungültig", str(fehler), parent=self)
            return

        self.ergebnis = self.einheit
        self.destroy()


class DatumsDialog(BasisDialog):
    """Einfache Kalenderauswahl ohne externe Bibliotheken."""

    MONATE = [
        "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember",
    ]

    def __init__(self, master, start: date) -> None:
        super().__init__(master, "Datum auswählen", breite=320, hoehe=330)
        self.aktuell = start
        self.kopf = ttk.Frame(self.body, style="Dialog.TFrame")
        self.kopf.grid(row=self.zeile, column=0, sticky="ew")
        self.zeile += 1
        self.gitter = ttk.Frame(self.body, style="Dialog.TFrame")
        self.gitter.grid(row=self.zeile, column=0, pady=(10, 0))
        self._aufbauen()

    def _aufbauen(self) -> None:
        for widget in list(self.kopf.winfo_children()) + list(self.gitter.winfo_children()):
            widget.destroy()

        ttk.Button(self.kopf, text="‹", width=3, style="Ghost.TButton",
                   command=lambda: self._blaettern(-1)).pack(side="left")
        ttk.Label(
            self.kopf,
            text=f"{self.MONATE[self.aktuell.month - 1]} {self.aktuell.year}",
            style="FieldLabel.TLabel",
        ).pack(side="left", expand=True)
        ttk.Button(self.kopf, text="›", width=3, style="Ghost.TButton",
                   command=lambda: self._blaettern(1)).pack(side="right")

        import calendar

        for i, name in enumerate(["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]):
            ttk.Label(self.gitter, text=name, style="Muted.TLabel", width=4,
                      anchor="center").grid(row=0, column=i)

        wochen = calendar.Calendar(firstweekday=0).monthdayscalendar(
            self.aktuell.year, self.aktuell.month
        )
        for r, woche in enumerate(wochen, start=1):
            for c, tag in enumerate(woche):
                if tag == 0:
                    continue
                ttk.Button(
                    self.gitter, text=str(tag), width=4, style="Ghost.TButton",
                    command=lambda t=tag: self._waehlen(t),
                ).grid(row=r, column=c, padx=1, pady=1)

    def _blaettern(self, delta: int) -> None:
        monat = self.aktuell.month + delta
        jahr = self.aktuell.year
        if monat < 1:
            monat, jahr = 12, jahr - 1
        elif monat > 12:
            monat, jahr = 1, jahr + 1
        self.aktuell = date(jahr, monat, 1)
        self._aufbauen()

    def _waehlen(self, tag: int) -> None:
        self.ergebnis = date(self.aktuell.year, self.aktuell.month, tag)
        self.destroy()

    def speichern(self) -> None:  # nicht benötigt
        self.destroy()
