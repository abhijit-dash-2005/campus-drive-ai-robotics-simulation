#!/usr/bin/env python3
"""Create three readable summary charts from every available evaluation CSV."""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUTPUT = ROOT / "graphs"
COLORS = ["#147D92", "#E07A35", "#6B63A8", "#4F8A5B", "#C34E63"]

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "figure.titlesize": 17,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#DDE4E8",
        "grid.linewidth": 0.8,
        "axes.axisbelow": True,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    }
)


def load_runs():
    runs = []
    for path in sorted(RESULTS.glob("campus_evaluation*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        stem = path.stem
        if stem == "campus_evaluation":
            base_label = "Latest saved"
        elif stem == "campus_evaluation_verified":
            base_label = "Verified"
        else:
            base_label = stem.removeprefix("campus_evaluation_").replace("_", " ").title()
        for index, row in enumerate(rows, start=1):
            label = base_label if len(rows) == 1 else f"{base_label} #{index}"
            runs.append(
                {
                    "label": label,
                    "source": path.name,
                    "elapsed": float(row["elapsed_seconds"]),
                    "path": float(row["path_length_m"]),
                    "minimum": float(row["minimum_obstacle_m"]),
                    "front": float(row["minimum_front_obstacle_m"]),
                    "scans": int(row["scan_count"]),
                    "near": int(row["near_obstacle_scans"]),
                    "stops": int(row["stop_commands"]),
                    "success": row["route_succeeded"].strip().lower() == "true",
                }
            )
    if not runs:
        raise SystemExit(f"No campus_evaluation*.csv files found in {RESULTS}")
    return runs


def save(fig, filename):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT / filename, dpi=180, bbox_inches="tight")
    plt.close(fig)


def run_labels(runs):
    return [f"{r['label']} · {'success' if r['success'] else 'incomplete'}" for r in runs]


def performance_chart(runs):
    labels = run_labels(runs)
    colors = [COLORS[i % len(COLORS)] for i in range(len(runs))]
    y = np.arange(len(runs))[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.4))
    fig.suptitle("Campus Drive AI — Route Performance", fontweight="bold", y=0.98)
    metrics = [
        ("elapsed", "Elapsed time", "seconds", "s"),
        ("path", "Distance traveled", "meters (odometry estimate)", "m"),
    ]
    for ax, (key, title, xlabel, unit) in zip(axes, metrics):
        values = [r[key] for r in runs]
        for yi, value, color in zip(y, values, colors):
            ax.scatter(value, yi, s=90, color=color, edgecolor="white", linewidth=1.2, zorder=3)
            ax.annotate(f"{value:.2f} {unit}", (value, yi), xytext=(9, 0),
                        textcoords="offset points", va="center", fontweight="bold", color="#24323A")
        ax.set_yticks(y, labels)
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_xlabel(xlabel)
        ax.set_xlim(0, max(values) * 1.30 if max(values) else 1)
        ax.set_ylim(-0.65, len(runs) - 0.35)
        ax.grid(axis="x")
        ax.grid(axis="y", visible=False)
    sources = ", ".join(dict.fromkeys(r["source"] for r in runs))
    fig.text(0.01, 0.015, f"Every CSV record is plotted. Source: results/{sources}", color="#53636D", fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 0.92))
    save(fig, "01_route_performance.png")


def lidar_chart(runs):
    fig, ax = plt.subplots(figsize=(9.7, 5.8))
    fig.suptitle("Campus Drive AI — LiDAR Range Observations", fontweight="bold", y=0.98)
    x_centers = np.arange(2)
    offsets = np.linspace(-0.12, 0.12, max(len(runs), 2))[: len(runs)]
    colors = [COLORS[i % len(COLORS)] for i in range(len(runs))]
    for run, offset, color in zip(runs, offsets, colors):
        for center, key in zip(x_centers, ("minimum", "front")):
            value = run[key]
            xpos = center + offset
            ax.scatter(xpos, value, s=95, color=color, edgecolor="white", linewidth=1.2, zorder=3,
                       label=run["label"] if center == 0 else "")
            ax.annotate(f"{value:.3f} m", (xpos, value), xytext=(0, 10 if offset >= 0 else -16),
                        textcoords="offset points", ha="center", fontsize=9, fontweight="bold", color="#24323A")
    ax.axhline(0.65, color="#A94442", linestyle="--", linewidth=1.6, label="0.65 m forward-trigger threshold")
    ax.set_xticks(x_centers, ["Minimum raw range\n(all directions)", "Minimum raw range\n(forward ±30°)"])
    ax.set_ylabel("Measured range (m)")
    ax.set_ylim(0, max(0.9, max(max(r["minimum"], r["front"]) for r in runs) + 0.22))
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, ncol=2, loc="upper left")
    sources = ", ".join(dict.fromkeys(r["source"] for r in runs))
    fig.text(0.01, 0.015,
             f"Each marker is one CSV record. Raw minima may include robot self-echo; dashed line is the controller trigger, not a safety guarantee. Source: results/{sources}",
             color="#53636D", fontsize=8)
    fig.tight_layout(rect=(0, 0.07, 1, 0.90))
    save(fig, "02_lidar_ranges.png")


def activity_chart(runs):
    labels = run_labels(runs)
    colors = [COLORS[i % len(COLORS)] for i in range(len(runs))]
    y = np.arange(len(runs))[::-1]
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.6))
    fig.suptitle("Campus Drive AI — Sensor and Controller Activity", fontweight="bold", y=0.98)
    panels = [
        ("scans", "LiDAR scans", "scan messages", lambda r: f"{r['scans']:,}"),
        ("near_pct", "Scans with raw return < 1 m", "share of scans", lambda r: f"{r['near']:,}/{r['scans']:,}  ({100*r['near']/r['scans']:.1f}%)"),
        ("stops", "Zero-velocity commands", "command samples", lambda r: f"{r['stops']:,}"),
    ]
    for ax, (key, title, xlabel, formatter) in zip(axes, panels):
        if key == "near_pct":
            values = [100 * r["near"] / r["scans"] if r["scans"] else 0 for r in runs]
            xmax = 105
        else:
            values = [r[key] for r in runs]
            xmax = max(values) * 1.45 if max(values) else 1
        for yi, value, run, color in zip(y, values, runs, colors):
            ax.scatter(value, yi, s=88, color=color, edgecolor="white", linewidth=1.2, zorder=3)
            label = formatter(run)
            ax.annotate(label, (value, yi), xytext=(8, 0), textcoords="offset points", va="center",
                        fontsize=8.5, fontweight="bold", color="#24323A")
        ax.set_yticks(y, labels)
        ax.set_title(title, loc="left", fontweight="bold", fontsize=10)
        ax.set_xlabel(xlabel)
        ax.set_xlim(0, xmax)
        ax.set_ylim(-0.65, len(runs) - 0.35)
        ax.grid(axis="x")
        ax.grid(axis="y", visible=False)
    sources = ", ".join(dict.fromkeys(r["source"] for r in runs))
    fig.text(0.01, 0.015, f"Near-range values are scan counts, not distinct obstacle encounters. Source: results/{sources}",
             color="#53636D", fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 0.91), w_pad=2)
    save(fig, "03_sensor_controller_activity.png")


def main():
    runs = load_runs()
    performance_chart(runs)
    lidar_chart(runs)
    activity_chart(runs)
    print(f"Created 3 charts from {len(runs)} successful/incomplete evaluation records in {OUTPUT}")
    for run in runs:
        print(f"{run['label']} ({run['source']}): success={run['success']}")


if __name__ == "__main__":
    main()
