#!/usr/bin/env python3

import argparse
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "fontcache"))

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path as MplPath

from delta_classification import BENCHMARKS, BENCHMARKS_TO_NAMES, DELTAS



plt.rcParams["ps.fonttype"] = 42
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['DejaVu Serif']  # default available

CHANGE_TYPE_COLORS = {
    "add": "#a1e2a1",
    "mod": "#ecebb2",
    "del": "#ecb5b2",
    "adddel": ("#a1e2a1", "#ecb5b2"),
    "addmod": ("#a1e2a1", "#ecebb2"),
    "delmod": ("#ecb5b2", "#ecebb2"),
}
DEFAULT_COLOR = "#999999"
INCR_EDGE = "black"


def bezier_point(t, p0, p1, p2, p3):
    u = 1 - t
    return (u**3) * p0 + 3 * (u**2) * t * p1 + 3 * u * (t**2) * p2 + (t**3) * p3


def bezier_polyline(p0, p1, p2, p3, steps=100):
    ts = np.linspace(0.0, 1.0, steps)
    return np.array([bezier_point(t, p0, p1, p2, p3) for t in ts])


def filled_bezier_band(ax, top_ps, bot_ps, color, alpha=0.35, steps=120, edge_lw=0.8):
    p0, p1, p2, p3 = top_ps
    q0, q1, q2, q3 = bot_ps

    top = bezier_polyline(p0, p1, p2, p3, steps=steps)
    bot = bezier_polyline(q0, q1, q2, q3, steps=steps)[::-1]
    poly = np.vstack([top, bot])

    codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(poly) - 1)
    patch = PathPatch(
        MplPath(poly, codes),
        facecolor=color,
        edgecolor=color,
        lw=edge_lw,
        alpha=alpha,
        zorder=3,
    )
    ax.add_patch(patch)

    for curve in (top, bot[::-1]):
        codes_line = [MplPath.MOVETO] + [MplPath.LINETO] * (len(curve) - 1)
        ax.add_patch(
            PathPatch(
                MplPath(curve, codes_line),
                facecolor="none",
                edgecolor=color,
                lw=0.9,
                alpha=0.9,
                zorder=4,
            )
        )


def load_series(csv_path: Path):
    if not csv_path.exists():
        return None

    df = pd.read_csv(csv_path)
    bash_times = df[df["mode"] == "bash"]["time_sec"].to_numpy()
    incr_times = df[df["mode"] == "incr"]["time_sec"].to_numpy()
    if len(bash_times) == 0 or len(incr_times) == 0:
        return None

    min_len = min(len(bash_times), len(incr_times))
    if min_len == 0:
        return None

    return bash_times[:min_len], incr_times[:min_len]


def plot_results(results_dir: Path, output_path: Path):
    fig, axes = plt.subplots(2, 7, figsize=(14, 3))
    axes = axes.flatten()

    for i, benchmark in enumerate(BENCHMARKS):
        ax = axes[i]
        series = load_series(results_dir / f"{benchmark}-time.csv")
        if series is None:
            ax.axis("off")
            continue

        bash_times, incr_times = series
        benchmark_deltas = DELTAS.get(benchmark, [])
        num_iters = min(len(bash_times), len(incr_times))

        x_left, x_right = 0.3, 1.0
        bar_width = 0.35
        ax.set_xlim(0, 1.35)

        bash_bottom = 0.0
        incr_bottom = 0.0

        for j in range(num_iters):
            if j < len(benchmark_deltas):
                change_type = benchmark_deltas[j]["change_type"]
                bash_color = CHANGE_TYPE_COLORS.get(change_type, DEFAULT_COLOR)
                incr_color = CHANGE_TYPE_COLORS.get(change_type, DEFAULT_COLOR)
            else:
                bash_color = DEFAULT_COLOR
                incr_color = DEFAULT_COLOR

            if isinstance(incr_color, tuple):
                left_c, right_c = incr_color
                ax.bar(x_right - bar_width / 4, incr_times[j], bar_width / 2, bottom=incr_bottom, color=left_c, edgecolor="none", linewidth=0.7, fill=True, zorder=2)
                ax.bar(x_right + bar_width / 4, incr_times[j], bar_width / 2, bottom=incr_bottom, color=right_c, edgecolor="none", linewidth=0.7, fill=True, zorder=2)
                ax.add_patch(
                    matplotlib.patches.Rectangle(
                        (x_right - bar_width / 2, incr_bottom),
                        bar_width,
                        incr_times[j],
                        fill=False,
                        edgecolor=INCR_EDGE,
                        linewidth=0.7,
                        zorder=3,
                    )
                )
            else:
                ax.bar(x_right, incr_times[j], bar_width, bottom=incr_bottom, color=incr_color, edgecolor="black", linewidth=0.7, fill=True, zorder=2)

            if isinstance(bash_color, tuple):
                left_c, right_c = bash_color
                ax.bar(x_left - bar_width / 4, bash_times[j], bar_width / 2, bottom=bash_bottom, color=left_c, edgecolor="none", linewidth=0.7, zorder=2)
                ax.bar(x_left + bar_width / 4, bash_times[j], bar_width / 2, bottom=bash_bottom, color=right_c, edgecolor="none", linewidth=0.7, zorder=2)
                ax.add_patch(
                    matplotlib.patches.Rectangle(
                        (x_left - bar_width / 2, bash_bottom),
                        bar_width,
                        bash_times[j],
                        fill=False,
                        edgecolor="black",
                        linewidth=0.7,
                        zorder=3,
                    )
                )
            else:
                ax.bar(x_left, bash_times[j], bar_width, bottom=bash_bottom, color=bash_color, edgecolor="black", linewidth=0.7, zorder=2)

            y_left_bot = bash_bottom
            y_right_bot = incr_bottom
            y_left_top = bash_bottom + bash_times[j]
            y_right_top = incr_bottom + incr_times[j]
            mid_x = (x_left + x_right) / 2.0

            p0 = np.array([x_left + bar_width / 2.0, y_left_top])
            p3 = np.array([x_right - bar_width / 2.0, y_right_top])
            p1 = np.array([mid_x - 0.10, y_left_top * 1.03])
            p2 = np.array([mid_x + 0.10, y_right_top * 1.03])

            q0 = np.array([x_left + bar_width / 2.0, y_left_bot])
            q3 = np.array([x_right - bar_width / 2.0, y_right_bot])
            q1 = np.array([mid_x - 0.10, y_left_bot * 1.03])
            q2 = np.array([mid_x + 0.10, y_right_bot * 1.03])

            filled_bezier_band(
                ax,
                top_ps=(p0, p1, p2, p3),
                bot_ps=(q0, q1, q2, q3),
                color=bash_color[0] if isinstance(bash_color, tuple) else bash_color,
                alpha=0.25,
                steps=140,
                edge_lw=0.6,
            )

            bash_bottom += bash_times[j]
            incr_bottom += incr_times[j]

        ax.set_title(BENCHMARKS_TO_NAMES[benchmark], fontsize=16)
        ax.tick_params(axis="y", labelsize=14)
        ax.set_xticks([])
        ax.set_xlabel("")

    fig.supylabel("Cumulative time (s)", fontsize=16)

    change_type_patches = [
        Patch(facecolor="none", edgecolor="none", label="Change Types:"),
        Patch(facecolor=CHANGE_TYPE_COLORS["add"], edgecolor="black", label="Addition"),
        Patch(facecolor=CHANGE_TYPE_COLORS["mod"], edgecolor="black", label="Modification"),
        Patch(facecolor=CHANGE_TYPE_COLORS["del"], edgecolor="black", label="Deletion"),
    ]
    mode_patches = [
        Patch(facecolor="none", edgecolor="none", label="Systems:"),
        Patch(facecolor="white", edgecolor="black", label="Bash (left bar)"),
        Patch(facecolor="white", edgecolor="black", label="Incr (right bar)"),
    ]

    fig.legend(
        handles=change_type_patches,
        loc="lower center",
        bbox_to_anchor=(0.27, -0.15),
        fontsize=14,
        ncols=4,
        title_fontsize=14,
        frameon=False,
    )
    fig.legend(
        handles=mode_patches,
        loc="lower center",
        bbox_to_anchor=(0.75, -0.15),
        fontsize=14,
        ncols=3,
        title_fontsize=14,
        frameon=False,
    )

    fig.tight_layout(rect=[0, 0.05, 1, 0.96])
    fig.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Saved {output_path}")


def main():
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent
    run_results_root = repo_root / "evaluation" / "run_results"
    figs_dir = repo_root / "evaluation" / "figs"
    figs_dir.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results-root",
        default=str(run_results_root),
        help="Root directory containing size subdirectories such as min or small.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(figs_dir),
        help="Directory where output PDFs will be written.",
    )
    args = parser.parse_args()

    results_root = Path(args.results_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    size_dirs = sorted(
        path for path in results_root.iterdir()
        if path.is_dir() and any(path.glob("*-time.csv"))
    )
    if not size_dirs:
        raise SystemExit(f"No result directories with *-time.csv found under {results_root}")

    script_stem = Path(__file__).stem
    for results_dir in size_dirs:
        output_path = output_dir / f"{script_stem}-{results_dir.name}.png"
        plot_results(results_dir, output_path)


if __name__ == "__main__":
    main()
