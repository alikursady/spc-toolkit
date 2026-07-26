import csv
from collections import Counter, OrderedDict
from pathlib import Path

import numpy as np

from spc.constants import MAX_SUBGROUP_SIZE, MIN_SUBGROUP_SIZE


class DataError(ValueError):
    pass


def load_subgroups(path: Path, subgroup_column: str = "subgroup",
                   value_column: str = "value") -> tuple[np.ndarray, list[str]]:
    """Read a long-format CSV into a (subgroups, subgroup size) array.

    Returns the array and the subgroup labels in the order they appeared.
    """
    grouped: "OrderedDict[str, list[float]]" = OrderedDict()

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise DataError(f"{path} is empty")
        missing = {subgroup_column, value_column} - set(reader.fieldnames)
        if missing:
            raise DataError(
                f"{path} is missing the column(s) {sorted(missing)}; "
                f"found {reader.fieldnames}"
            )

        for line_number, row in enumerate(reader, start=2):
            raw = row[value_column]
            try:
                value = float(raw)
            except (TypeError, ValueError):
                raise DataError(
                    f"{path}:{line_number} has a non-numeric measurement {raw!r}"
                ) from None
            grouped.setdefault(row[subgroup_column], []).append(value)

    if not grouped:
        raise DataError(f"{path} has a header but no rows")

    sizes = {len(values) for values in grouped.values()}
    if len(sizes) > 1:
        expected = Counter(len(v) for v in grouped.values()).most_common(1)[0][0]
        odd = [label for label, values in grouped.items() if len(values) != expected]
        raise DataError(
            f"every subgroup must be the same size; most hold {expected} readings "
            f"but {len(odd)} do not (first few: {odd[:5]})"
        )

    size = sizes.pop()
    if not MIN_SUBGROUP_SIZE <= size <= MAX_SUBGROUP_SIZE:
        raise DataError(
            f"subgroup size {size} is outside the supported range "
            f"{MIN_SUBGROUP_SIZE}-{MAX_SUBGROUP_SIZE}"
        )

    return np.array(list(grouped.values()), dtype=float), list(grouped.keys())
