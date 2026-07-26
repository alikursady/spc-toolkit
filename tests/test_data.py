import pytest

from spc.data import DataError, load_subgroups


def write(tmp_path, text, name="m.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_rows_are_grouped_in_the_order_they_appear(tmp_path):
    path = write(tmp_path, "subgroup,value\nB,1\nB,2\nA,3\nA,4\n")

    subgroups, labels = load_subgroups(path)

    assert labels == ["B", "A"]
    assert subgroups.tolist() == [[1.0, 2.0], [3.0, 4.0]]


def test_column_names_can_be_overridden(tmp_path):
    path = write(tmp_path, "batch,reading\n1,5\n1,6\n2,7\n2,8\n")

    subgroups, _ = load_subgroups(path, subgroup_column="batch", value_column="reading")

    assert subgroups.tolist() == [[5.0, 6.0], [7.0, 8.0]]


def test_missing_column_names_the_columns_it_did_find(tmp_path):
    path = write(tmp_path, "group,value\n1,5\n")

    with pytest.raises(DataError, match="subgroup"):
        load_subgroups(path)


def test_non_numeric_measurement_reports_the_line(tmp_path):
    path = write(tmp_path, "subgroup,value\n1,5\n1,oops\n")

    with pytest.raises(DataError, match="3"):
        load_subgroups(path)


def test_ragged_subgroups_are_rejected(tmp_path):
    path = write(tmp_path, "subgroup,value\n1,5\n1,6\n2,7\n")

    with pytest.raises(DataError, match="same size"):
        load_subgroups(path)


def test_subgroup_larger_than_the_constant_table_is_rejected(tmp_path):
    rows = "".join(f"1,{i}\n" for i in range(11)) + "".join(f"2,{i}\n" for i in range(11))
    path = write(tmp_path, "subgroup,value\n" + rows)

    with pytest.raises(DataError, match="outside the supported range"):
        load_subgroups(path)


def test_header_without_rows_is_rejected(tmp_path):
    path = write(tmp_path, "subgroup,value\n")

    with pytest.raises(DataError, match="no rows"):
        load_subgroups(path)


def test_the_bundled_sample_loads(tmp_path):
    from pathlib import Path

    sample = Path(__file__).resolve().parent.parent / "data" / "shaft-diameter.csv"
    subgroups, labels = load_subgroups(sample)

    assert subgroups.shape == (25, 5)
    assert len(labels) == 25
