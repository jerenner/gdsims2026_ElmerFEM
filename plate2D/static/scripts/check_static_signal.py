#!/usr/bin/env python3
"""Check the static prompt signal against the 1D parallel-plate estimate."""

from __future__ import annotations

import re
from pathlib import Path


E_CHARGE_FC = 1.602176634e-4
ELECTRON_START_Y_CM = 1.45
ELECTRON_SPEED_CM_NS = 0.05


def activity_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "geometry" / "ppc_geometry.geo").exists():
            return parent
    raise RuntimeError("Could not locate the plate2D/static activity root.")


def read_geo_parameter(path: Path, name: str) -> float:
    pattern = re.compile(rf"^\s*{re.escape(name)}\s*=\s*([0-9.eE+-]+)\s*;")
    with path.open() as handle:
        for line in handle:
            match = pattern.match(line)
            if match:
                return float(match.group(1))
    raise RuntimeError(f"Could not find '{name}' in {path}.")


def read_signal(path: Path) -> list[tuple[float, float]]:
    rows = []
    with path.open() as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            t, signal = line.split()[:2]
            rows.append((float(t), float(signal)))
    if len(rows) < 2:
        raise RuntimeError(f"Need at least two signal rows in {path}.")
    return rows


def read_resistive_epsilon(path: Path) -> float:
    in_material_1 = False
    pattern = re.compile(r"Relative Permittivity\s*=\s*([0-9.eE+-]+)")
    with path.open() as handle:
        for line in handle:
            stripped = line.strip()
            if stripped == "Material 1":
                in_material_1 = True
                continue
            if in_material_1 and stripped == "End":
                break
            if in_material_1:
                match = pattern.search(stripped)
                if match:
                    return float(match.group(1))
    raise RuntimeError(f"Could not find Material 1 Relative Permittivity in {path}.")


def main() -> None:
    root = activity_root()
    signal_file = root / "output" / "garfield" / "signal_static.dat"
    geo_file = root / "geometry" / "ppc_geometry.geo"
    sif_file = root / "elmer" / "weighting_field.sif"

    rows = read_signal(signal_file)
    dt = rows[1][0] - rows[0][0]
    charge_fc = sum(signal * dt for _, signal in rows)

    gap = read_geo_parameter(geo_file, "gap")
    layer = read_geo_parameter(geo_file, "layer")
    epsilon_r = read_resistive_epsilon(sif_file)
    prompt_field = epsilon_r / (layer + epsilon_r * gap)
    drift_distance = ELECTRON_START_Y_CM - layer
    collection_time = drift_distance / ELECTRON_SPEED_CM_NS
    expected_e = -prompt_field * drift_distance

    print(f"Integrated signal: {charge_fc / E_CHARGE_FC:.6f} e")
    print(f"1D static estimate: {expected_e:.6f} e")
    print(f"Prompt weighting field in gas: {prompt_field:.6f} 1/cm")
    print(f"Expected collection time: {collection_time:.3f} ns")


if __name__ == "__main__":
    main()
