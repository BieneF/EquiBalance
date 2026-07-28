"""Ansicht: Dashboard (FA-15) – Überblick über den aktuellen Trainingsstand."""

from __future__ import annotations

from datetime import date, timedelta
from tkinter import ttk

from ..config import COLORS
from ..widgets_helpers import format_datum  # noqa: F401  (Kompatibilität)
from .widgets import Card, KennzahlCard, Kalenderansicht, RingDiagramm


class DashboardView(ttk.Frame):
    """Startseite mit Kennzahlen, letzten Einheiten und Top-Hinweisen."""

    titel = "Dashboard"

    def __init__(self, master, app) -> None:
        super().__init__(master, style="Content.TFrame")
        self.app = app

        kpi = ttk.Frame(self, style="Content.TFrame")
        kpi.pack(fill="x")
        for i in range(4):
            kpi.columnconfigure(i, weight=1, uniform="kpi")

        self.kpi_einheiten = KennzahlCard(kpi, "Einheiten (21 Tage)", "0")
        self.kpi_dauer = KennzahlCard(kpi, "Ø Dauer", "0", "min")
        self.kpi_frequenz = KennzahlCard(kpi, "Häufigkeit", "0", "/ Woche")
        self.kpi_balance = KennzahlCard(kpi, "Trainingsbalance", "0", "/ 100")
        for i, karte in enumerate(
            [self.kpi_einheiten, self.kpi_dauer, self.kpi_frequenz, self.kpi_balance]
        ):
            karte.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 10, 0))

        mitte = ttk.Frame(self, style="Content.TFrame")
        mitte.pack(fill="both", expand=True, pady=(16, 0))
        mitte.columnconfigure(0, weight=3, uniform="d")
        mitte.columnconfigure(1, weight=2, uniform="d")
        mitte.rowconfigure(0, weight=1)

        links = ttk.Frame(mitte, style="Content.TFrame")
        links.grid(row=0, column=0, sticky="nsew")

        karte_letzte = Card(links, "Letzte Trainingseinheiten")
        karte_letzte.pack(fill="both", expand=True)
        self.tabelle = ttk.Treeview(
            karte_letzte,
            columns=("datum", "art", "dauer", "intensitaet", "schwerpunkt"),
            show="headings",
            height=7,
        )
        for spalte, text, breite in [
            ("datum", "Datum", 90),
            ("art", "Trainingsart", 120),
            ("dauer", "Dauer", 70),
            ("intensitaet", "Intensität", 90),
            ("schwerpunkt", "Schwerpunkt", 130),
        ]:
            self.tabelle.heading(spalte, text=text)
            self.tabelle.column(spalte, width=breite, anchor="w")
        self.tabelle.pack(fill="both", expand=True)

        karte_woche = Card(links, "Trainingstage der letzten 12 Wochen")
        karte_woche.pack(fill="x", pady=(16, 0))
        self.kalender = Kalenderansicht(karte_woche)
        self.kalender.pack(fill="x")

        rechts = ttk.Frame(mitte, style="Content.TFrame")
        rechts.grid(row=0, column=1, sticky="nsew", padx=(16, 0))

        karte_ring = Card(rechts, "Trainingsarten (21 Tage)")
        karte_ring.pack(fill="x")
        self.ring = RingDiagramm(karte_ring, height=190)
        self.ring.pack(fill="x")

        karte_hinweise = Card(rechts, "Hinweise und Empfehlungen")
        karte_hinweise.pack(fill="both", expand=True, pady=(16, 0))
        self.hinweise = ttk.Frame(karte_hinweise, style="Card.TFrame")
        self.hinweise.pack(fill="both", expand=True)

    # ------------------------------------------------------------ Aktualisierung
    def aktualisieren(self) -> None:
        pferd = self.app.aktuelles_pferd
        for widget in self.hinweise.winfo_children():
            widget.destroy()
        self.tabelle.delete(*self.tabelle.get_children())

        if pferd is None:
            self.kpi_einheiten.setze("–")
            self.kpi_dauer.setze("–")
            self.kpi_frequenz.setze("–")
            self.kpi_balance.setze("–")
            self.ring.setze_daten({})
            self.kalender.setze_tage({})
            ttk.Label(
                self.hinweise,
                text="Bitte legen Sie zunächst ein Pferd in der Pferdeverwaltung an.",
                style="Muted.TLabel", wraplength=280,
            ).pack(anchor="w")
            return

        einheiten = self.app.trainingseinheiten()
        analyse = self.app.analyse()

        self.kpi_einheiten.setze(str(analyse.anzahl_zeitraum))
        self.kpi_dauer.setze(f"{analyse.durchschnittsdauer:g}")
        self.kpi_frequenz.setze(f"{analyse.haeufigkeit_pro_woche:g}")
        self.kpi_balance.setze(f"{analyse.ausgewogenheitsindex:g}")

        for e in einheiten[:7]:
            self.tabelle.insert(
                "", "end",
                values=(
                    e.datum.strftime("%d.%m.%Y"),
                    e.trainingsart,
                    f"{e.dauer} min",
                    e.intensitaet,
                    e.schwerpunkt,
                ),
            )

        self.ring.setze_daten(analyse.verteilung_arten)
        self.kalender.setze_tage(self._kalenderdaten(einheiten))

        for empfehlung in self.app.empfehlungen()[:4]:
            block = ttk.Frame(self.hinweise, style="Card.TFrame")
            block.pack(fill="x", pady=(0, 10))
            kopf = ttk.Frame(block, style="Card.TFrame")
            kopf.pack(fill="x")
            ttk.Label(kopf, text=empfehlung.titel, style="HinweisTitel.TLabel",
                      wraplength=260).pack(anchor="w")
            ttk.Label(block, text=empfehlung.text, style="Muted.TLabel",
                      wraplength=280).pack(anchor="w", pady=(2, 0))

    @staticmethod
    def _kalenderdaten(einheiten, wochen: int = 12) -> dict:
        heute = date.today()
        start = heute - timedelta(days=heute.weekday() + 7 * (wochen - 1))
        summen: dict[str, int] = {}
        for i in range(wochen * 7):
            tag = start + timedelta(days=i)
            summen[tag.isoformat()] = 0
        for e in einheiten:
            key = e.datum.isoformat()
            if key in summen:
                summen[key] += e.dauer
        # spaltenweise (je Woche) sortieren
        geordnet: dict[str, int] = {}
        for w in range(wochen):
            for d in range(7):
                tag = start + timedelta(days=w * 7 + d)
                geordnet[tag.isoformat()] = summen.get(tag.isoformat(), 0)
        return geordnet
