from pathlib import Path

from spc.cli import EXIT_BAD_INPUT, EXIT_OK, EXIT_OUT_OF_CONTROL, main

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "shaft-diameter.csv"


def test_sample_data_is_flagged_and_writes_a_chart(tmp_path, capsys):
    chart = tmp_path / "chart.png"

    code = main([str(SAMPLE), "--lsl", "11.970", "--usl", "12.030",
                 "--chart", str(chart)])

    assert code == EXIT_OUT_OF_CONTROL
    assert chart.exists() and chart.stat().st_size > 0
    out = capsys.readouterr().out
    assert "Cpk" in out
    assert "Rule 1" in out


def test_report_can_be_written_to_a_file(tmp_path, capsys):
    report = tmp_path / "nested" / "summary.txt"

    main([str(SAMPLE), "--no-chart", "--report", str(report)])

    assert report.exists()
    assert "Control limits" in report.read_text(encoding="utf-8")


def test_capability_is_omitted_without_spec_limits(tmp_path, capsys):
    main([str(SAMPLE), "--no-chart"])

    out = capsys.readouterr().out
    assert "Capability" not in out
    assert "Control limits" in out


def test_one_spec_limit_alone_is_an_error(capsys):
    code = main([str(SAMPLE), "--no-chart", "--lsl", "11.97"])

    assert code == EXIT_BAD_INPUT
    assert "both" in capsys.readouterr().err


def test_missing_file_is_reported_cleanly(tmp_path, capsys):
    code = main([str(tmp_path / "nope.csv"), "--no-chart"])

    assert code == EXIT_BAD_INPUT
    assert "no such file" in capsys.readouterr().err


def test_a_stable_process_exits_zero(tmp_path, capsys):
    # Eight subgroups that alternate around the centre, short enough and calm
    # enough that no rule has anything to say.
    rows = ["subgroup,value"]
    pattern = [(-1, 0, 1), (1, 0, -1)]
    for g in range(1, 9):
        for offset in pattern[g % 2]:
            rows.append(f"{g},{10 + offset * 0.1}")
    csv = tmp_path / "stable.csv"
    csv.write_text("\n".join(rows) + "\n", encoding="utf-8")

    assert main([str(csv), "--no-chart"]) == EXIT_OK
