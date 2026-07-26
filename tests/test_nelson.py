import numpy as np
import pytest

from spc.nelson import evaluate, out_of_control_points
from spc.statistics import ControlLimits

# Centre 0, three sigma at 3, so a value equals its own sigma count.
LIMITS = ControlLimits(center=0.0, lower=-3.0, upper=3.0)


def rules_fired(values):
    return {violation.rule for violation in evaluate(np.array(values, dtype=float), LIMITS)}


def test_quiet_process_triggers_nothing():
    # Alternating small values, short enough not to trip the run-length rules.
    values = [0.5, -0.4, 0.3, -0.5, 0.4, -0.3, 0.2, -0.2]

    assert rules_fired(values) == set()


def test_rule1_catches_a_point_past_three_sigma():
    values = [0.1, -0.2, 3.5, 0.2, -0.1]

    violations = evaluate(np.array(values), LIMITS)
    rule1 = next(v for v in violations if v.rule == 1)
    assert rule1.indices == (2,)


def test_rule1_ignores_a_point_exactly_on_the_limit():
    assert 1 not in rules_fired([0.1, 3.0, -0.1])


def test_rule2_needs_nine_on_the_same_side():
    assert 2 not in rules_fired([0.2] * 8)
    assert 2 in rules_fired([0.2] * 9)


def test_rule2_is_not_fooled_by_a_point_on_the_centre_line():
    # A value of exactly zero is on neither side, so the run is broken.
    assert 2 not in rules_fired([0.2, 0.2, 0.2, 0.2, 0.0, 0.2, 0.2, 0.2, 0.2])


def test_rule3_needs_six_monotonic_points():
    assert 3 not in rules_fired([0.1, 0.2, 0.3, 0.4, 0.5])
    assert 3 in rules_fired([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    assert 3 in rules_fired([0.6, 0.5, 0.4, 0.3, 0.2, 0.1])


def test_rule3_is_broken_by_a_repeated_value():
    assert 3 not in rules_fired([0.1, 0.2, 0.2, 0.3, 0.4, 0.5])


def test_rule4_needs_fourteen_alternating_points():
    zigzag = [0.5 if i % 2 == 0 else -0.5 for i in range(14)]

    assert 4 in rules_fired(zigzag)
    assert 4 not in rules_fired(zigzag[:13])


def test_rule5_flags_only_the_points_past_two_sigma():
    values = [0.1, 2.5, 0.4, 2.6, 0.1]

    rule5 = next(v for v in evaluate(np.array(values), LIMITS) if v.rule == 5)
    assert rule5.indices == (1, 3)


def test_rule5_ignores_two_points_on_opposite_sides():
    assert 5 not in rules_fired([2.5, 0.1, -2.6])


def test_rule6_needs_four_of_five_beyond_one_sigma():
    assert 6 in rules_fired([1.2, 1.3, 0.2, 1.4, 1.5])
    assert 6 not in rules_fired([1.2, 1.3, 0.2, 0.3, 1.5])


def test_rule7_catches_fifteen_points_hugging_the_centre():
    assert 7 in rules_fired([0.3, -0.2] * 8)
    assert 7 not in rules_fired([0.3, -0.2] * 7)


def test_rule8_needs_eight_points_outside_one_sigma_on_either_side():
    assert 8 in rules_fired([1.5, -1.6, 1.7, -1.8, 1.5, -1.6, 1.7, -1.8])
    assert 8 not in rules_fired([1.5, -1.6, 1.7, 0.5, 1.5, -1.6, 1.7, -1.8])


def test_out_of_control_points_merges_indices_across_rules():
    values = np.array([0.1, 3.5, 3.6, 0.2])

    points = out_of_control_points(evaluate(values, LIMITS))

    assert {1, 2} <= points


def test_sigma_scaling_uses_the_supplied_limits():
    # Limits ten times wider, so the same raw value is a tenth of the sigma count.
    wide = ControlLimits(center=0.0, lower=-30.0, upper=30.0)

    assert evaluate(np.array([3.5, 0.1, 0.2]), wide) == []


@pytest.mark.parametrize("length", [0, 1, 2])
def test_series_too_short_for_any_rule_returns_no_violations(length):
    assert evaluate(np.zeros(length), LIMITS) == []
