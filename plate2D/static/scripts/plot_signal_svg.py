#!/usr/bin/env python3

from pathlib import Path
import sys


def read_signal(path: Path):
    points = []
    with path.open() as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            t, s = line.split()[:2]
            points.append((float(t), float(s)))
    return points


def make_svg(points, title: str) -> str:
    width, height = 820, 520
    left, right, top, bottom = 80, 30, 50, 70
    plot_w = width - left - right
    plot_h = height - top - bottom

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if ymin == ymax:
      ymin -= 1.0
      ymax += 1.0
    pad = 0.05 * (ymax - ymin)
    ymin -= pad
    ymax += pad

    def px(x):
        return left + (x - xmin) / (xmax - xmin) * plot_w

    def py(y):
        return top + (ymax - y) / (ymax - ymin) * plot_h

    path_data = " ".join(
        ("M" if i == 0 else "L") + f" {px(x):.2f} {py(y):.2f}"
        for i, (x, y) in enumerate(points)
    )

    xticks = 5
    yticks = 5
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fcfbf8"/>',
        f'<text x="{width / 2:.1f}" y="28" text-anchor="middle" font-size="20" font-family="Helvetica, Arial, sans-serif">{title}</text>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#333" stroke-width="1.5"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#333" stroke-width="1.5"/>',
    ]
    for i in range(xticks + 1):
        value = xmin + i * (xmax - xmin) / xticks
        x = px(value)
        parts.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#ddd" stroke-width="1"/>')
        parts.append(f'<text x="{x:.2f}" y="{top + plot_h + 24}" text-anchor="middle" font-size="13" font-family="Helvetica, Arial, sans-serif">{value:.0f}</text>')
    for i in range(yticks + 1):
        value = ymin + i * (ymax - ymin) / yticks
        y = py(value)
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#ddd" stroke-width="1"/>')
        parts.append(f'<text x="{left - 10}" y="{y + 5:.2f}" text-anchor="end" font-size="13" font-family="Helvetica, Arial, sans-serif">{value:.2e}</text>')
    parts.extend([
        f'<path d="{path_data}" fill="none" stroke="#0f766e" stroke-width="2.5"/>',
        f'<text x="{left + plot_w / 2:.1f}" y="{height - 20}" text-anchor="middle" font-size="15" font-family="Helvetica, Arial, sans-serif">time [ns]</text>',
        f'<text x="22" y="{top + plot_h / 2:.1f}" text-anchor="middle" font-size="15" font-family="Helvetica, Arial, sans-serif" transform="rotate(-90 22 {top + plot_h / 2:.1f})">signal [fC / ns]</text>',
        '</svg>',
    ])
    return "\n".join(parts)


def main():
    if len(sys.argv) != 3:
        print("Usage: plot_signal_svg.py input.dat output.svg")
        return 1
    points = read_signal(Path(sys.argv[1]))
    svg = make_svg(points, "Prompt Signal from the Static Weighting Potential")
    Path(sys.argv[2]).write_text(svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
