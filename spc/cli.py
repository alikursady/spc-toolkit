import argparse
import sys
from pathlib import Path

from spc import charts, report
from spc.constants import UnsupportedSubgroupSize
from spc.data import DataError, load_subgroups
from spc.nelson import evaluate, out_of_control_points
from spc.statistics import capability, chart_statistics

EXIT_OK = 0
EXIT_OUT_OF_CONTROL = 1
EXIT_BAD_INPUT = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spc",
        description="Build an X-bar/R control chart from measurement data and "
                    "report process capability.",
    )
    parser.add_argument("csv", type=Path, help="long-format CSV of measurements")
    parser.add_argument("--lsl", type=float, help="lower specification limit")
    parser.add_argument("--usl", type=float, help="upper specification limit")
    parser.add_argument("--chart", type=Path, default=Path("out/control-chart.png"),
                        help="where to write the PNG (default: %(default)s)")
    parser.add_argument("--report", type=Path,
                        help="also write the summary to this file")
    parser.add_argument("--subgroup-column", default="subgroup")
    parser.add_argument("--value-column", default="value")
    parser.add_argument("--title", default=None, help="chart title")
    parser.add_argument("--no-chart", action="store_true",
                        help="skip the PNG and only print the summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if (args.lsl is None) != (args.usl is None):
        print("give both --lsl and --usl, or neither", file=sys.stderr)
        return EXIT_BAD_INPUT

    try:
        subgroups, _ = load_subgroups(args.csv, args.subgroup_column, args.value_column)
        stats = chart_statistics(subgroups)
        spec = capability(stats, args.lsl, args.usl) if args.lsl is not None else None
    except (DataError, UnsupportedSubgroupSize, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_BAD_INPUT
    except FileNotFoundError:
        print(f"error: no such file: {args.csv}", file=sys.stderr)
        return EXIT_BAD_INPUT

    violations = evaluate(stats.means, stats.xbar_limits)
    flagged = out_of_control_points(violations)

    summary = report.build(stats, spec, violations, str(args.csv))
    print(summary, end="")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(summary, encoding="utf-8")
        print(f"\nreport written to {args.report}")

    if not args.no_chart:
        written = charts.write_control_chart(
            stats, flagged, args.chart,
            title=args.title or f"X-bar and R chart - {args.csv.stem}")
        print(f"chart written to {written}")

    # A non-zero exit lets this drop into a pipeline that should stop when the
    # process is not in control.
    return EXIT_OUT_OF_CONTROL if violations else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
