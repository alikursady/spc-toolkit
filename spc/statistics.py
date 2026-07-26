from dataclasses import dataclass

import numpy as np

from spc.constants import a2, d2, d3, d4


@dataclass(frozen=True)
class ControlLimits:
    center: float
    lower: float
    upper: float

    def sigma(self) -> float:
        """Control limits sit at three sigma, so one sigma is a third of the arm."""
        return (self.upper - self.center) / 3.0


@dataclass(frozen=True)
class ChartStatistics:
    subgroup_size: int
    subgroup_count: int
    means: np.ndarray
    ranges: np.ndarray
    grand_mean: float
    mean_range: float
    xbar_limits: ControlLimits
    r_limits: ControlLimits
    sigma_within: float
    sigma_overall: float


@dataclass(frozen=True)
class Capability:
    cp: float
    cpk: float
    pp: float
    ppk: float
    lsl: float
    usl: float


def chart_statistics(subgroups: np.ndarray) -> ChartStatistics:
    """subgroups is a 2-D array shaped (number of subgroups, subgroup size)."""
    if subgroups.ndim != 2:
        raise ValueError("expected a 2-D array of subgroups")
    if subgroups.shape[0] < 2:
        raise ValueError("at least two subgroups are needed to estimate variation")

    n = subgroups.shape[1]
    means = subgroups.mean(axis=1)
    ranges = subgroups.max(axis=1) - subgroups.min(axis=1)

    grand_mean = float(means.mean())
    mean_range = float(ranges.mean())

    xbar_arm = a2(n) * mean_range
    xbar_limits = ControlLimits(grand_mean, grand_mean - xbar_arm, grand_mean + xbar_arm)
    r_limits = ControlLimits(mean_range, d3(n) * mean_range, d4(n) * mean_range)

    sigma_within = mean_range / d2(n)
    # ddof=1 because the data is a sample of the process, not the population.
    sigma_overall = float(subgroups.ravel().std(ddof=1))

    return ChartStatistics(
        subgroup_size=n,
        subgroup_count=subgroups.shape[0],
        means=means,
        ranges=ranges,
        grand_mean=grand_mean,
        mean_range=mean_range,
        xbar_limits=xbar_limits,
        r_limits=r_limits,
        sigma_within=sigma_within,
        sigma_overall=sigma_overall,
    )


def capability(stats: ChartStatistics, lsl: float, usl: float) -> Capability:
    """Cp/Cpk use the within-subgroup sigma estimated from the average range;
    Pp/Ppk use the overall sample sigma. The pair diverges when the process
    drifts between subgroups, which is the whole point of reporting both."""
    if usl <= lsl:
        raise ValueError("the upper spec limit must be above the lower one")
    if stats.sigma_within <= 0 or stats.sigma_overall <= 0:
        raise ValueError("cannot compute capability when the spread is zero")

    tolerance = usl - lsl
    mean = stats.grand_mean

    return Capability(
        cp=tolerance / (6.0 * stats.sigma_within),
        cpk=min(usl - mean, mean - lsl) / (3.0 * stats.sigma_within),
        pp=tolerance / (6.0 * stats.sigma_overall),
        ppk=min(usl - mean, mean - lsl) / (3.0 * stats.sigma_overall),
        lsl=lsl,
        usl=usl,
    )
