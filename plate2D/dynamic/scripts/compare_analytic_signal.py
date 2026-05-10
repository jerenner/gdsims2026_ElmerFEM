#!/usr/bin/env python3
"""Compare the transient Garfield++ signal with the 1D analytic EQS result.

The analytic result is the parallel-plate conductive-layer solution discussed
in Riegler's time-dependent weighting-field treatment. For a gas gap of
thickness d2 above a resistive layer of thickness d1, the gas weighting field is

  E_w(t) = er / (d1 + er d2)
           + d1 / (d2 (d1 + er d2)) (1 - exp(-t / tau)),

while the electron is drifting. After the electron reaches the resistive
surface, the prompt part stops and the delayed term relaxes exponentially.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt
import os
from pathlib import Path
import re

CACHE_ROOT = Path(os.environ.get("TMPDIR", "/tmp")) / "gdsims2026_python_cache"
MPLCONFIGDIR = CACHE_ROOT / "matplotlib"
XDG_CACHE_HOME = CACHE_ROOT / "xdg"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
XDG_CACHE_HOME.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR))
os.environ.setdefault("XDG_CACHE_HOME", str(XDG_CACHE_HOME))

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ModuleNotFoundError as exc:
    raise SystemExit(
        "This script needs matplotlib. On the VM, install it with "
        "'sudo apt install python3-matplotlib' if it is not already available."
    ) from exc


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


SignalRows = list[tuple[float, float, float, float]]


def activity_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "geometry" / "ppc_geometry.geo").exists():
            return parent
    raise RuntimeError("Could not locate the plate2D/dynamic activity root.")


def read_signal(path: Path) -> SignalRows:
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


def write_analytic_table(
    path: Path, rows: SignalRows, pars: AnalyticParameters
) -> SignalRows:
    analytic = []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as out:
        out.write("# time_ns total_fC_per_ns prompt_fC_per_ns delayed_fC_per_ns\n")
        for t, *_ in rows:
            total, prompt, delayed = analytic_components(t, pars)
            analytic.append((t, total, prompt, delayed))
            out.write(f"{t:.8g} {total:.12e} {prompt:.12e} {delayed:.12e}\n")
    return analytic


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def make_plot(
    path: Path,
    garfield_rows: SignalRows,
    analytic_rows: SignalRows,
    pars: AnalyticParameters,
) -> None:
    del pars
    fig, ax = plt.subplots(figsize=(7.2, 4.9), dpi=180)
    ax.plot(
        [t for t, _, _, _ in garfield_rows],
        [total for _, total, _, _ in garfield_rows],
        color="#1f4aa8",
        linewidth=2.2,
        label="Garfield++ + Elmer EQS",
    )
    ax.plot(
        [t for t, _, _, _ in analytic_rows],
        [total for _, total, _, _ in analytic_rows],
        color="#d97706",
        linewidth=2.0,
        linestyle="--",
        label="1D analytic",
    )
    ax.axvline(19.0, color="0.45", linestyle=":", linewidth=1.5)
    ax.text(
        0.53,
        0.57,
        "electron reaches layer at T = 19.0 ns",
        transform=ax.transAxes,
        fontsize=10,
    )
    ax.set_xlim(0.0, 100.0)
    ax.set_ylim(-8.2e-6, 0.7e-6)
    ax.set_xlabel("time [ns]")
    ax.set_ylabel("signal [fC / ns]")
    ax.legend(frameon=False, loc="lower right")
    save_figure(fig, path)


def make_transient_signal_plot(path: Path, garfield_rows: SignalRows) -> None:
    xmax = 50.0
    window_rows = [row for row in garfield_rows if row[0] <= xmax]
    if not window_rows:
        raise RuntimeError("No signal samples found in the 0-50 ns plotting window.")

    values = [
        value
        for _, total, prompt, delayed in window_rows
        for value in (total, prompt, delayed)
    ]
    ymin = 1.12 * min(values)
    ymax = max(0.7e-6, 1.12 * max(values))

    fig, ax = plt.subplots(figsize=(7.2, 4.9), dpi=180)
    ax.plot(
        [t for t, _, _, _ in window_rows],
        [total for _, total, _, _ in window_rows],
        color="#1f4aa8",
        linewidth=2.2,
        label="total",
    )
    ax.plot(
        [t for t, _, _, _ in window_rows],
        [prompt for _, _, prompt, _ in window_rows],
        color="0.35",
        linewidth=1.8,
        linestyle="--",
        label="prompt",
    )
    ax.plot(
        [t for t, _, _, _ in window_rows],
        [delayed for _, _, _, delayed in window_rows],
        color="#d97706",
        linewidth=1.8,
        label="delayed",
    )
    ax.axvline(19.0, color="0.45", linestyle=":", linewidth=1.5)
    ax.text(
        0.52,
        0.57,
        "electron reaches layer at T = 19.0 ns",
        transform=ax.transAxes,
        fontsize=10,
    )
    ax.set_xlim(0.0, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("time [ns]")
    ax.set_ylabel("signal [fC / ns]")
    ax.legend(frameon=False, loc="lower right")
    save_figure(fig, path)


def make_tail_zoom_plot(
    path: Path,
    garfield_rows: SignalRows,
    analytic_rows: SignalRows,
    pars: AnalyticParameters,
) -> None:
    dt = garfield_rows[1][0] - garfield_rows[0][0]
    full_xmax = garfield_rows[-1][0] + 0.5 * dt
    tail_xmax = 19.0 + 8.0 * relaxation_time_ns(pars)
    xmax = min(full_xmax, max(200.0, tail_xmax))
    delayed_values = [delayed for _, _, _, delayed in garfield_rows]
    ymin = 1.12 * min(delayed_values)
    ymax = max(0.3e-8, 0.08 * abs(ymin))

    fig, ax = plt.subplots(figsize=(7.2, 4.9), dpi=180)
    ax.plot(
        [t for t, _, _, _ in garfield_rows],
        [delayed for _, _, _, delayed in garfield_rows],
        color="#1f4aa8",
        linewidth=2.2,
        label="Garfield++ delayed",
    )
    sampled_analytic = analytic_rows[::20]
    ax.scatter(
        [t for t, _, _, _ in sampled_analytic],
        [delayed for _, _, _, delayed in sampled_analytic],
        color="#d97706",
        s=12,
        label="1D analytic delayed",
        zorder=3,
    )
    ax.axvline(19.0, color="0.45", linestyle=":", linewidth=1.5)
    ax.text(
        0.17,
        0.84,
        rf"$\tau = {relaxation_time_ns(pars):.2f}$ ns",
        transform=ax.transAxes,
        fontsize=10,
    )
    ax.set_xlim(0.0, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("time [ns]")
    ax.set_ylabel("delayed signal [fC / ns]")
    ax.legend(frameon=False, loc="lower right")
    save_figure(fig, path)


def print_residuals(
    garfield_rows: SignalRows,
    analytic_rows: SignalRows,
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


def print_integrals(rows: SignalRows) -> None:
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
