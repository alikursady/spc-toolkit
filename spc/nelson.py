"""The eight Nelson rules, applied to the X-bar chart.

Each rule returns the zero-based indices of the points it flags. A point can be
flagged by more than one rule; nothing here deduplicates.
"""
from dataclasses import dataclass
from typing import Callable

import numpy as np

from spc.statistics import ControlLimits


@dataclass(frozen=True)
class Violation:
    rule: int
    description: str
    indices: tuple[int, ...]


def _zones(values: np.ndarray, limits: ControlLimits) -> np.ndarray:
    """Signed distance from the centre line in sigma units."""
    return (values - limits.center) / limits.sigma()


def _rule1(z: np.ndarray) -> list[int]:
    return [i for i, v in enumerate(z) if abs(v) > 3]


def _rule2(z: np.ndarray) -> list[int]:
    return _run_on_one_side(z, length=9)


def _rule3(z: np.ndarray) -> list[int]:
    flagged: set[int] = set()
    for i in range(len(z) - 5):
        window = z[i:i + 6]
        diffs = np.diff(window)
        if np.all(diffs > 0) or np.all(diffs < 0):
            flagged.update(range(i, i + 6))
    return sorted(flagged)


def _rule4(z: np.ndarray) -> list[int]:
    flagged: set[int] = set()
    for i in range(len(z) - 13):
        window = z[i:i + 14]
        diffs = np.diff(window)
        if np.any(diffs == 0):
            continue
        signs = np.sign(diffs)
        if np.all(signs[1:] != signs[:-1]):
            flagged.update(range(i, i + 14))
    return sorted(flagged)


def _rule5(z: np.ndarray) -> list[int]:
    return _k_of_m_beyond(z, k=2, m=3, threshold=2)


def _rule6(z: np.ndarray) -> list[int]:
    return _k_of_m_beyond(z, k=4, m=5, threshold=1)


def _rule7(z: np.ndarray) -> list[int]:
    flagged: set[int] = set()
    for i in range(len(z) - 14):
        if np.all(np.abs(z[i:i + 15]) < 1):
            flagged.update(range(i, i + 15))
    return sorted(flagged)


def _rule8(z: np.ndarray) -> list[int]:
    flagged: set[int] = set()
    for i in range(len(z) - 7):
        if np.all(np.abs(z[i:i + 8]) > 1):
            flagged.update(range(i, i + 8))
    return sorted(flagged)


def _run_on_one_side(z: np.ndarray, length: int) -> list[int]:
    flagged: set[int] = set()
    for i in range(len(z) - length + 1):
        window = z[i:i + length]
        if np.all(window > 0) or np.all(window < 0):
            flagged.update(range(i, i + length))
    return sorted(flagged)


def _k_of_m_beyond(z: np.ndarray, k: int, m: int, threshold: float) -> list[int]:
    """k out of m consecutive points beyond `threshold` sigma on the same side.

    Only the points actually past the threshold are flagged, not the whole
    window, because the points inside it are not themselves suspicious.
    """
    flagged: set[int] = set()
    for i in range(len(z) - m + 1):
        window = z[i:i + m]
        for sign in (1, -1):
            beyond = [i + j for j, v in enumerate(window) if sign * v > threshold]
            if len(beyond) >= k:
                flagged.update(beyond)
    return sorted(flagged)


_RULES: list[tuple[int, str, Callable[[np.ndarray], list[int]]]] = [
    (1, "One point beyond three sigma", _rule1),
    (2, "Nine points in a row on the same side of the centre line", _rule2),
    (3, "Six points in a row steadily increasing or decreasing", _rule3),
    (4, "Fourteen points in a row alternating up and down", _rule4),
    (5, "Two of three consecutive points beyond two sigma on the same side", _rule5),
    (6, "Four of five consecutive points beyond one sigma on the same side", _rule6),
    (7, "Fifteen points in a row within one sigma", _rule7),
    (8, "Eight points in a row beyond one sigma on either side", _rule8),
]


def evaluate(values: np.ndarray, limits: ControlLimits) -> list[Violation]:
    z = _zones(np.asarray(values, dtype=float), limits)
    violations = []
    for number, description, check in _RULES:
        indices = check(z)
        if indices:
            violations.append(Violation(number, description, tuple(indices)))
    return violations


def out_of_control_points(violations: list[Violation]) -> set[int]:
    return {index for violation in violations for index in violation.indices}
