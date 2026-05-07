#!/usr/bin/env python3

from __future__ import annotations

import os
from pathlib import Path
import sys

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


def read_signal(path: Path) -> list[tuple[float, float]]:
    points = []
    with path.open() as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            t, s = line.split()[:2]
            points.append((float(t), float(s)))
    if not points:
        raise RuntimeError(f"No signal samples found in {path}.")
    return points


def make_plot(points: list[tuple[float, float]], output: Path) -> None:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ymin, ymax = min(ys), max(ys)
    if ymin == ymax:
        ymin -= 1.0
        ymax += 1.0
    pad = 0.08 * (ymax - ymin)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.2, 4.9), dpi=180)
    ax.plot(xs, ys, color="#0f766e", linewidth=2.2)
    ax.set_title("Prompt Signal from the Static Weighting Potential")
    ax.set_xlabel("time [ns]")
    ax.set_ylabel("signal [fC / ns]")
    ax.set_xlim(min(xs), max(xs))
    ax.set_ylim(ymin - pad, ymax + pad)
    ax.grid(True, color="0.88", linewidth=0.8)
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: plot_signal.py input.dat output.png")
        return 1
    make_plot(read_signal(Path(sys.argv[1])), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
