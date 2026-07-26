from pathlib import Path

import matplotlib

# Agg has no display dependency, which matters when this runs on a CI runner.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (must follow the backend choice)

from spc.statistics import ChartStatistics  # noqa: E402

OUT_OF_CONTROL_COLOUR = "#c0392b"
IN_CONTROL_COLOUR = "#2c3e50"


def _panel(axis, values, limits, title, ylabel, flagged):
    positions = range(1, len(values) + 1)
    axis.plot(positions, values, marker="o", markersize=4,
              color=IN_CONTROL_COLOUR, linewidth=1.2, zorder=2)

    if flagged:
        axis.scatter([p + 1 for p in flagged], [values[p] for p in flagged],
                     color=OUT_OF_CONTROL_COLOUR, s=55, zorder=3, label="flagged")

    axis.axhline(limits.center, color="#27ae60", linewidth=1.2)
    axis.axhline(limits.upper, color=OUT_OF_CONTROL_COLOUR, linestyle="--", linewidth=1.0)
    axis.axhline(limits.lower, color=OUT_OF_CONTROL_COLOUR, linestyle="--", linewidth=1.0)

    axis.annotate(f"UCL {limits.upper:.4f}", xy=(1.005, limits.upper),
                  xycoords=("axes fraction", "data"), fontsize=8, va="center")
    axis.annotate(f"CL {limits.center:.4f}", xy=(1.005, limits.center),
                  xycoords=("axes fraction", "data"), fontsize=8, va="center")
    axis.annotate(f"LCL {limits.lower:.4f}", xy=(1.005, limits.lower),
                  xycoords=("axes fraction", "data"), fontsize=8, va="center")

    axis.set_title(title, fontsize=11, loc="left")
    axis.set_ylabel(ylabel)
    axis.grid(alpha=0.25)


def write_control_chart(stats: ChartStatistics, flagged: set[int], path: Path,
                        title: str = "X-bar and R chart") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    figure, (top, bottom) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    figure.suptitle(title, fontsize=13, x=0.09, ha="left")

    _panel(top, stats.means, stats.xbar_limits,
           f"Subgroup average (n = {stats.subgroup_size})", "mean", flagged)
    # Nelson rules are evaluated on the averages only, so the range panel never
    # carries flags of its own here.
    _panel(bottom, stats.ranges, stats.r_limits, "Subgroup range", "range", set())

    bottom.set_xlabel("subgroup")
    figure.tight_layout(rect=(0, 0, 0.9, 0.96))
    figure.savefig(path, dpi=140)
    plt.close(figure)
    return path
