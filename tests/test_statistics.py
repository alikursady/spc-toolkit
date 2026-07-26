import numpy as np
import pytest

from spc.constants import UnsupportedSubgroupSize, factors
from spc.statistics import capability, chart_statistics


def test_factors_match_the_published_table():
    assert factors(5) == (2.326, 0.577, 0.0, 2.114)
    assert factors(2)[3] == 3.267


def test_unsupported_subgroup_size_is_rejected():
    with pytest.raises(UnsupportedSubgroupSize):
        factors(11)


def test_limits_are_computed_from_the_average_range():
    # Two subgroups with a known mean and range make the arithmetic checkable
    # by hand: means 2 and 4, ranges 2 and 2, so R-bar is 2 and X-bar-bar is 3.
    subgroups = np.array([[1.0, 2.0, 3.0], [3.0, 4.0, 5.0]])

    stats = chart_statistics(subgroups)

    assert stats.grand_mean == pytest.approx(3.0)
    assert stats.mean_range == pytest.approx(2.0)
    # A2 for n=3 is 1.023
    assert stats.xbar_limits.upper == pytest.approx(3.0 + 1.023 * 2.0)
    assert stats.xbar_limits.lower == pytest.approx(3.0 - 1.023 * 2.0)
    # D3 is 0 and D4 is 2.574 for n=3
    assert stats.r_limits.lower == pytest.approx(0.0)
    assert stats.r_limits.upper == pytest.approx(2.574 * 2.0)
    # d2 for n=3 is 1.693
    assert stats.sigma_within == pytest.approx(2.0 / 1.693)


def test_sigma_is_one_third_of_the_control_arm():
    stats = chart_statistics(np.array([[1.0, 2.0, 3.0], [3.0, 4.0, 5.0]]))

    limits = stats.xbar_limits
    assert limits.sigma() == pytest.approx((limits.upper - limits.center) / 3)


def test_a_single_subgroup_cannot_estimate_variation():
    with pytest.raises(ValueError):
        chart_statistics(np.array([[1.0, 2.0, 3.0]]))


def test_one_dimensional_input_is_rejected():
    with pytest.raises(ValueError):
        chart_statistics(np.array([1.0, 2.0, 3.0]))


def test_cp_uses_the_tolerance_over_six_sigma():
    subgroups = np.array([[9.0, 10.0, 11.0], [9.0, 10.0, 11.0]])
    stats = chart_statistics(subgroups)

    result = capability(stats, lsl=7.0, usl=13.0)

    assert result.cp == pytest.approx(6.0 / (6 * stats.sigma_within))
    # Centred process, so Cpk equals Cp.
    assert result.cpk == pytest.approx(result.cp)


def test_cpk_drops_when_the_process_sits_off_centre():
    centred = chart_statistics(np.array([[9.0, 10.0, 11.0], [9.0, 10.0, 11.0]]))
    offset = chart_statistics(np.array([[10.0, 11.0, 12.0], [10.0, 11.0, 12.0]]))

    centred_result = capability(centred, lsl=7.0, usl=13.0)
    offset_result = capability(offset, lsl=7.0, usl=13.0)

    assert offset_result.cp == pytest.approx(centred_result.cp)
    assert offset_result.cpk < centred_result.cpk


def test_cp_exceeds_pp_when_subgroups_shift_relative_to_each_other():
    # Same spread inside each subgroup, but the second sits well above the
    # first, so the overall sigma is larger than the within-subgroup one.
    subgroups = np.array([[9.0, 10.0, 11.0], [19.0, 20.0, 21.0]])

    result = capability(chart_statistics(subgroups), lsl=0.0, usl=30.0)

    assert result.cp > result.pp
    assert result.cpk > result.ppk


def test_inverted_spec_limits_are_rejected():
    stats = chart_statistics(np.array([[1.0, 2.0, 3.0], [3.0, 4.0, 5.0]]))

    with pytest.raises(ValueError):
        capability(stats, lsl=10.0, usl=5.0)
