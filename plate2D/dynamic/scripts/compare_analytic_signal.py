#!/usr/bin/env python3
"""Compare the transient Garfield++ signal with the 1D analytic EQS result.

The analytic result is the parallel-plate conductive-layer solution discussed
in Riegler's time-dependent weighting-field treatment.  For a gas gap of
thickness d2 above a resistive layer of thickness d1, the gas weighting field is

  E_w(t) = er / (d1 + er d2)
           + d1 / (d2 (d1 + er d2)) (1 - exp(-t / tau)),

while the electron is drifting.  After the electron reaches the resistive
surface, the prompt part stops and the delayed term relaxes exponentially.
"""

from __future__ import annotations

from array import array
from dataclasses import dataclass
from math import exp, sqrt
from pathlib import Path
import re

import ROOT


@dataclass(frozen=True)
class AnalyticParameters:
    resistive_thickness_cm: float = 0.5
    gas_gap_cm: float = 1.0
    resistive_epsilon_r: float = 2.0
    gas_epsilon_r: float = 1.0
    resistive_conductivity_s_m: float = 1.0e-3
    gas_conductivity_s_m: float = 1.0e-12
    electron_start_y_cm: float = 1.45
    gas_resistive_interface_y_cm: float = 0.5
    electron_speed_cm_ns: float = 0.05


E_CHARGE_FC = 1.602176634e-4
EPS0_F_M = 8.854187817e-12


def activity_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "geometry" / "ppc_geometry.geo").exists():
            return parent
    raise RuntimeError("Could not locate the plate2D/dynamic activity root.")


def read_signal(path: Path) -> list[tuple[float, float, float, float]]:
    rows = []
    with path.open() as infile:
        for line in infile:
            if not line.strip() or line.startswith("#"):
                continue
            t, total, prompt, delayed = map(float, line.split())
            rows.append((t, total, prompt, delayed))
    if not rows:
        raise RuntimeError(f"No signal rows found in {path}.")
    return rows


def read_material_value(root: Path, material_id: int, key: str) -> float:
    sif = root / "elmer" / "weighting_dynamic_eqs.sif"
    in_material = False
    pattern = re.compile(rf"{re.escape(key)}\s*=\s*([0-9.eE+-]+)")
    with sif.open() as handle:
        for line in handle:
            stripped = line.strip()
            if stripped == f"Material {material_id}":
                in_material = True
                continue
            if in_material and stripped == "End":
                break
            if in_material:
                match = pattern.search(stripped)
                if match:
                    return float(match.group(1))
    raise RuntimeError(f"Could not read Material {material_id} {key} from {sif}.")


def analytic_components(
    t_ns: float, pars: AnalyticParameters
) -> tuple[float, float, float]:
    d1 = pars.resistive_thickness_cm
    d2 = pars.gas_gap_cm
    er = pars.resistive_epsilon_r
    speed = pars.electron_speed_cm_ns

    # Prompt field in the gas from the dielectric electrostatic solution.
    prompt_field = er / (d1 + er * d2)
    # Amplitude of the conductive relaxation correction in the gas.
    delayed_field_amplitude = d1 / (d2 * (d1 + er * d2))

    tau_ns = relaxation_time_ns(pars)
    drift_time_ns = (
        pars.electron_start_y_cm - pars.gas_resistive_interface_y_cm
    ) / speed

    prompt = -E_CHARGE_FC * speed * prompt_field if t_ns < drift_time_ns else 0.0
    if t_ns < drift_time_ns:
        delayed = (
            -E_CHARGE_FC
            * speed
            * delayed_field_amplitude
            * (1.0 - exp(-t_ns / tau_ns))
        )
    else:
        delayed_at_collection = delayed_field_amplitude * (
            1.0 - exp(-drift_time_ns / tau_ns)
        )
        delayed = (
            -E_CHARGE_FC
            * speed
            * delayed_at_collection
            * exp(-(t_ns - drift_time_ns) / tau_ns)
        )
    return prompt + delayed, prompt, delayed


def relaxation_time_ns(pars: AnalyticParameters) -> float:
    d1_m = pars.resistive_thickness_cm * 1.0e-2
    d2_m = pars.gas_gap_cm * 1.0e-2
    capacitance_per_area = (
        pars.resistive_epsilon_r * EPS0_F_M / d1_m
        + pars.gas_epsilon_r * EPS0_F_M / d2_m
    )
    conductance_per_area = (
        pars.resistive_conductivity_s_m / d1_m
        + pars.gas_conductivity_s_m / d2_m
    )
    return 1.0e9 * capacitance_per_area / conductance_per_area


def write_analytic_table(
    path: Path, rows: list[tuple[float, float, float, float]], pars: AnalyticParameters
) -> list[tuple[float, float, float, float]]:
    analytic = []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as out:
        out.write("# time_ns total_fC_per_ns prompt_fC_per_ns delayed_fC_per_ns\n")
        for t, *_ in rows:
            total, prompt, delayed = analytic_components(t, pars)
            analytic.append((t, total, prompt, delayed))
            out.write(f"{t:.8g} {total:.12e} {prompt:.12e} {delayed:.12e}\n")
    return analytic


def graph(points: list[tuple[float, float]], name: str, color: int, width: int,
          style: int = 1) -> ROOT.TGraph:
    xs = array("d", [p[0] for p in points])
    ys = array("d", [p[1] for p in points])
    gr = ROOT.TGraph(len(points), xs, ys)
    gr.SetName(name)
    gr.SetLineColor(color)
    gr.SetLineWidth(width)
    gr.SetLineStyle(style)
    return gr


def marker_graph(points: list[tuple[float, float]], name: str, color: int,
                 marker: int = 20) -> ROOT.TGraph:
    xs = array("d", [p[0] for p in points])
    ys = array("d", [p[1] for p in points])
    gr = ROOT.TGraph(len(points), xs, ys)
    gr.SetName(name)
    gr.SetMarkerColor(color)
    gr.SetMarkerStyle(marker)
    gr.SetMarkerSize(0.85)
    return gr


def make_plot(
    path: Path,
    garfield_rows: list[tuple[float, float, float, float]],
    analytic_rows: list[tuple[float, float, float, float]],
    pars: AnalyticParameters,
) -> None:
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)

    canvas = ROOT.TCanvas("cAnalyticOverlay", "Analytic signal comparison", 950, 650)
    frame = ROOT.TH1D("frame", "", 100, 0.0, 100.0)
    frame.SetDirectory(0)
    frame.SetMinimum(-8.2e-6)
    frame.SetMaximum(0.7e-6)
    frame.GetXaxis().SetTitle("time [ns]")
    frame.GetYaxis().SetTitle("signal [fC / ns]")
    frame.GetXaxis().SetTitleSize(0.045)
    frame.GetYaxis().SetTitleSize(0.045)
    frame.Draw()

    garfield_total = graph(
        [(t, total) for t, total, _, _ in garfield_rows],
        "garfield_total",
        ROOT.kBlue + 2,
        4,
    )
    analytic_total = graph(
        [(t, total) for t, total, _, _ in analytic_rows],
        "analytic_total",
        ROOT.kOrange + 7,
        5,
        7,
    )
    garfield_total.Draw("L SAME")
    analytic_total.Draw("L SAME")

    collection = ROOT.TLine(19.0, -8.2e-6, 19.0, 0.7e-6)
    collection.SetLineColor(ROOT.kGray + 1)
    collection.SetLineStyle(3)
    collection.SetLineWidth(2)
    collection.Draw()

    legend = ROOT.TLegend(0.52, 0.70, 0.88, 0.82)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.AddEntry(garfield_total, "Garfield++ + Elmer EQS", "l")
    legend.AddEntry(analytic_total, "1D analytic", "l")
    legend.Draw()

    text = ROOT.TLatex()
    text.SetNDC(True)
    text.SetTextSize(0.032)
    text.DrawLatex(0.53, 0.57, "electron reaches layer at T = 19.0 ns")

    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.SaveAs(str(path))


def make_transient_signal_plot(
    path: Path,
    garfield_rows: list[tuple[float, float, float, float]],
) -> None:
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)

    xmax = 50.0
    window_rows = [row for row in garfield_rows if row[0] <= xmax]
    if not window_rows:
        raise RuntimeError("No signal samples found in the 0-50 ns plotting window.")

    values = [value for _, total, prompt, delayed in window_rows
              for value in (total, prompt, delayed)]
    ymin = 1.12 * min(values)
    ymax = max(0.7e-6, 1.12 * max(values))

    canvas = ROOT.TCanvas("cTransientSignal", "Transient signal", 950, 650)
    frame = ROOT.TH1D("transientFrame", "", 100, 0.0, xmax)
    frame.SetDirectory(0)
    frame.SetMinimum(ymin)
    frame.SetMaximum(ymax)
    frame.GetXaxis().SetTitle("time [ns]")
    frame.GetYaxis().SetTitle("signal [fC / ns]")
    frame.GetXaxis().SetTitleSize(0.045)
    frame.GetYaxis().SetTitleSize(0.045)
    frame.Draw()

    total_graph = graph(
        [(t, total) for t, total, _, _ in garfield_rows],
        "garfield_total_short",
        ROOT.kBlue + 2,
        4,
    )
    prompt_graph = graph(
        [(t, prompt) for t, _, prompt, _ in garfield_rows],
        "garfield_prompt_short",
        ROOT.kGray + 2,
        3,
        2,
    )
    delayed_graph = graph(
        [(t, delayed) for t, _, _, delayed in garfield_rows],
        "garfield_delayed_short",
        ROOT.kOrange + 7,
        3,
    )
    total_graph.Draw("L SAME")
    prompt_graph.Draw("L SAME")
    delayed_graph.Draw("L SAME")

    collection = ROOT.TLine(19.0, ymin, 19.0, ymax)
    collection.SetLineColor(ROOT.kGray + 1)
    collection.SetLineStyle(3)
    collection.SetLineWidth(2)
    collection.Draw()

    legend = ROOT.TLegend(0.50, 0.65, 0.88, 0.84)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.AddEntry(total_graph, "total", "l")
    legend.AddEntry(prompt_graph, "prompt", "l")
    legend.AddEntry(delayed_graph, "delayed", "l")
    legend.Draw()

    text = ROOT.TLatex()
    text.SetNDC(True)
    text.SetTextSize(0.032)
    text.DrawLatex(0.52, 0.57, "electron reaches layer at T = 19.0 ns")

    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.SaveAs(str(path))


def make_tail_zoom_plot(
    path: Path,
    garfield_rows: list[tuple[float, float, float, float]],
    analytic_rows: list[tuple[float, float, float, float]],
    pars: AnalyticParameters,
) -> None:
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)

    dt = garfield_rows[1][0] - garfield_rows[0][0]
    full_xmax = garfield_rows[-1][0] + 0.5 * dt
    tail_xmax = 19.0 + 8.0 * relaxation_time_ns(pars)
    xmax = min(full_xmax, max(200.0, tail_xmax))
    delayed_values = [delayed for _, _, _, delayed in garfield_rows]
    ymin = 1.12 * min(delayed_values)
    ymax = max(0.3e-8, 0.08 * abs(ymin))

    canvas = ROOT.TCanvas("cTailZoom", "Delayed tail comparison", 950, 650)
    frame = ROOT.TH1D("tailFrame", "", 100, 0.0, xmax)
    frame.SetDirectory(0)
    frame.SetMinimum(ymin)
    frame.SetMaximum(ymax)
    frame.GetXaxis().SetTitle("time [ns]")
    frame.GetYaxis().SetTitle("delayed signal [fC / ns]")
    frame.GetXaxis().SetTitleSize(0.045)
    frame.GetYaxis().SetTitleSize(0.045)
    frame.Draw()

    garfield_delayed = graph(
        [(t, delayed) for t, _, _, delayed in garfield_rows],
        "garfield_delayed",
        ROOT.kBlue + 2,
        4,
    )
    analytic_delayed = marker_graph(
        [(t, delayed) for t, _, _, delayed in analytic_rows[::20]],
        "analytic_delayed_zoom",
        ROOT.kOrange + 7,
        20,
    )
    garfield_delayed.Draw("L SAME")
    analytic_delayed.Draw("P SAME")

    collection = ROOT.TLine(19.0, ymin, 19.0, ymax)
    collection.SetLineColor(ROOT.kGray + 1)
    collection.SetLineStyle(3)
    collection.SetLineWidth(2)
    collection.Draw()

    legend = ROOT.TLegend(0.52, 0.20, 0.88, 0.35)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.AddEntry(garfield_delayed, "Garfield++ delayed", "l")
    legend.AddEntry(analytic_delayed, "1D analytic delayed", "p")
    legend.Draw()

    text = ROOT.TLatex()
    text.SetNDC(True)
    text.SetTextSize(0.032)
    text.DrawLatex(0.17, 0.84, f"#tau = {relaxation_time_ns(pars):.2f} ns")

    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.SaveAs(str(path))


def print_residuals(
    garfield_rows: list[tuple[float, float, float, float]],
    analytic_rows: list[tuple[float, float, float, float]],
    pars: AnalyticParameters,
) -> None:
    diffs = []
    for garfield, analytic in zip(garfield_rows, analytic_rows):
        diffs.append(tuple(g - a for g, a in zip(garfield[1:], analytic[1:])))
    n = len(diffs)
    rms_total = sqrt(sum(d[0] * d[0] for d in diffs) / n)
    max_total = max(abs(d[0]) for d in diffs)
    max_prompt = max(abs(d[1]) for d in diffs)
    max_delayed = max(abs(d[2]) for d in diffs)
    print(f"Analytic relaxation time: {relaxation_time_ns(pars):.4f} ns")
    print(f"Compared {n} Garfield++ time bins.")
    print(f"Total signal RMS residual: {rms_total:.3e} fC/ns")
    print(f"Total signal max residual: {max_total:.3e} fC/ns")
    print(f"Prompt max residual:       {max_prompt:.3e} fC/ns")
    print(f"Delayed max residual:      {max_delayed:.3e} fC/ns")


def print_integrals(rows: list[tuple[float, float, float, float]]) -> None:
    dt = rows[1][0] - rows[0][0]
    total = sum(row[1] * dt for row in rows) / E_CHARGE_FC
    prompt = sum(row[2] * dt for row in rows) / E_CHARGE_FC
    delayed = sum(row[3] * dt for row in rows) / E_CHARGE_FC
    print(f"Garfield integral, total:   {total:.6f} e")
    print(f"Garfield integral, prompt:  {prompt:.6f} e")
    print(f"Garfield integral, delayed: {delayed:.6f} e")


def main() -> None:
    root = activity_root()
    signal_file = root / "output" / "garfield" / "signal_transient.dat"
    analytic_file = root / "output" / "garfield" / "signal_transient_analytic.dat"
    plot_file = root / "figures" / "signal_transient_analytic_overlay.png"
    docs_plot_file = root / "docs" / "figures" / "signal_transient_analytic_overlay.png"
    zoom_file = root / "figures" / "signal_transient_tail_zoom.png"
    docs_zoom_file = root / "docs" / "figures" / "signal_transient_tail_zoom.png"
    signal_plot_file = root / "figures" / "signal_transient.png"
    docs_signal_plot_file = root / "docs" / "figures" / "signal_transient.png"

    pars = AnalyticParameters(
        resistive_conductivity_s_m=read_material_value(
            root, 1, "Electric Conductivity"
        ),
        resistive_epsilon_r=read_material_value(root, 1, "Relative Permittivity"),
    )
    garfield_rows = read_signal(signal_file)
    analytic_rows = write_analytic_table(analytic_file, garfield_rows, pars)
    make_transient_signal_plot(signal_plot_file, garfield_rows)
    make_transient_signal_plot(docs_signal_plot_file, garfield_rows)
    make_plot(plot_file, garfield_rows, analytic_rows, pars)
    make_plot(docs_plot_file, garfield_rows, analytic_rows, pars)
    make_tail_zoom_plot(zoom_file, garfield_rows, analytic_rows, pars)
    make_tail_zoom_plot(docs_zoom_file, garfield_rows, analytic_rows, pars)
    print_residuals(garfield_rows, analytic_rows, pars)
    print_integrals(garfield_rows)
    print(f"Wrote {analytic_file}")
    print(f"Wrote {signal_plot_file}")
    print(f"Wrote {docs_signal_plot_file}")
    print(f"Wrote {plot_file}")
    print(f"Wrote {docs_plot_file}")
    print(f"Wrote {zoom_file}")
    print(f"Wrote {docs_zoom_file}")


if __name__ == "__main__":
    main()
