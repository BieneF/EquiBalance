"""Ansicht: Analyse (FA-09 bis FA-14) – grafische Auswertungen."""

from __future__ import annotations

from tkinter import ttk

from ..widgets_helpers import format_minuten
from .widgets import (
    BalkenDiagramm,
    Card,
    IndexAnzeige,
    KennzahlCard,
    SaeulenDiagramm,
)


class AnalyseView(ttk.Frame):
    """Stellt Verteilungen, Häufigkeiten und den Ausgewogenheitsindex dar."""

    titel = "Analyse"

    def __init__(self, master, app) -> None:
        super().__init__(master, style="Content.TFrame")
        self.app = app

        kpi = ttk.Frame(self, style="Content.TFrame")
        kpi.pack(fill="x")
        for i in range(4):
            kpi.columnconfigure(i, weight=1, uniform="k")

        self.kpi_gesamt = KennzahlCard(kpi, "Einheiten gesamt", "0")
        self.kpi_zeit = KennzahlCard(kpi, "Trainingszeit gesamt", "0", "min")
        self.kpi_luecke = KennzahlCard(kpi, "Trainingslücken", "0", "Arten")
        self.kpi_letzte = KennzahlCard(kpi, "Letztes Training", "–")
        for i, karte in enumerate(
            [self.kpi_gesamt, self.kpi_zeit, self.kpi_luecke, self.kpi_letzte]
        ):
            karte.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 10, 0))

        gitter = ttk.Frame(self, style="Content.TFrame")
        gitter.pack(fill="both", expand=True, pady=(16, 0))
        gitter.columnconfigure(0, weight=1, uniform="g")
        gitter.columnconfigure(1, weight=1, uniform="g")
        gitter.rowconfigure(0, weight=1)
        gitter.rowconfigure(1, weight=1)

        karte_arten = Card(gitter, "Verteilung der Trainingsarten (21 Tage)")
        karte_arten.grid(row=0, column=0, sticky="nsew")
        self.diagramm_arten = BalkenDiagramm(karte_arten, einheit="x", height=200)
        self.diagramm_arten.pack(fill="both", expand=True)

        karte_sp = Card(gitter, "Verteilung der Schwerpunkte (21 Tage)")
        karte_sp.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        self.diagramm_sp = BalkenDiagramm(karte_sp, einheit="x", height=200)
        self.diagramm_sp.pack(fill="both", expand=True)

        karte_woche = Card(gitter, "Trainingsminuten pro Woche")
        karte_woche.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        self.diagramm_woche = SaeulenDiagramm(karte_woche, height=200)
        self.diagramm_woche.pack(fill="both", expand=True)

        karte_index = Card(gitter, "Ausgewogenheit und Belastung")
        karte_index.grid(row=1, column=1, sticky="nsew", padx=(16, 0), pady=(16, 0))
        self.index = IndexAnzeige(karte_index, height=130)
        self.index.pack(fill="x")
        self.diagramm_intensitaet = BalkenDiagramm(karte_index, einheit="x", height=90)
        self.diagramm_intensitaet.pack(fill="both", expand=True, pady=(6, 0))

    def aktualisieren(self) -> None:
        if self.app.aktuelles_pferd is None:
            for diagramm in (self.diagramm_arten, self.diagramm_sp,
                             self.diagramm_woche, self.diagramm_intensitaet):
                diagramm.setze_daten({})
            self.index.setze_wert(0)
            self.kpi_gesamt.setze("–")
            self.kpi_zeit.setze("–")
            self.kpi_luecke.setze("–")
            self.kpi_letzte.setze("–")
            return

        analyse = self.app.analyse()
        self.kpi_gesamt.setze(str(analyse.anzahl_gesamt))
        self.kpi_zeit.setze(format_minuten(analyse.minuten_gesamt), "")
        self.kpi_luecke.setze(str(len(analyse.trainingsluecken)))
        self.kpi_letzte.setze(
            analyse.letztes_training.strftime("%d.%m.%Y")
            if analyse.letztes_training else "–", ""
        )

        self.diagramm_arten.setze_daten(analyse.verteilung_arten)
        self.diagramm_sp.setze_daten(analyse.verteilung_schwerpunkte)
        self.diagramm_woche.setze_daten(analyse.minuten_pro_woche)
        self.diagramm_intensitaet.setze_daten(analyse.verteilung_intensitaet)
        self.index.setze_wert(analyse.ausgewogenheitsindex)
