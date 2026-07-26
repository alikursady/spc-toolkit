"""Shewhart control chart constants.

Values are the standard ones tabulated in ASTM STP-15D / ISO 7870, indexed by
subgroup size. d2 is the bias correction used to turn an average range into a
within-subgroup standard deviation.
"""

# n: (d2, A2, D3, D4)
_TABLE = {
    2: (1.128, 1.880, 0.0, 3.267),
    3: (1.693, 1.023, 0.0, 2.574),
    4: (2.059, 0.729, 0.0, 2.282),
    5: (2.326, 0.577, 0.0, 2.114),
    6: (2.534, 0.483, 0.0, 2.004),
    7: (2.704, 0.419, 0.076, 1.924),
    8: (2.847, 0.373, 0.136, 1.864),
    9: (2.970, 0.337, 0.184, 1.816),
    10: (3.078, 0.308, 0.223, 1.777),
}

MIN_SUBGROUP_SIZE = min(_TABLE)
MAX_SUBGROUP_SIZE = max(_TABLE)


class UnsupportedSubgroupSize(ValueError):
    pass


def factors(n: int) -> tuple[float, float, float, float]:
    """Return (d2, A2, D3, D4) for subgroup size n."""
    try:
        return _TABLE[n]
    except KeyError:
        raise UnsupportedSubgroupSize(
            f"subgroup size {n} is outside the tabulated range "
            f"{MIN_SUBGROUP_SIZE}-{MAX_SUBGROUP_SIZE}"
        ) from None


def d2(n: int) -> float:
    return factors(n)[0]


def a2(n: int) -> float:
    return factors(n)[1]


def d3(n: int) -> float:
    return factors(n)[2]


def d4(n: int) -> float:
    return factors(n)[3]
