from spc.nelson import Violation
from spc.statistics import Capability, ChartStatistics


def _verdict(cpk: float) -> str:
    if cpk < 1.0:
        return "not capable, the spread does not fit inside the tolerance"
    if cpk < 1.33:
        return "marginal, most customers ask for at least 1.33"
    if cpk < 1.67:
        return "capable"
    return "capable with room to spare"


def build(stats: ChartStatistics, capability: Capability | None,
          violations: list[Violation], source: str) -> str:
    lines = [
        f"Source            {source}",
        f"Subgroups         {stats.subgroup_count} of size {stats.subgroup_size}",
        f"Measurements      {stats.subgroup_count * stats.subgroup_size}",
        "",
        "Control limits",
        f"  X-bar           CL {stats.grand_mean:.4f}  "
        f"LCL {stats.xbar_limits.lower:.4f}  UCL {stats.xbar_limits.upper:.4f}",
        f"  Range           CL {stats.mean_range:.4f}  "
        f"LCL {stats.r_limits.lower:.4f}  UCL {stats.r_limits.upper:.4f}",
        "",
        "Variation",
        f"  sigma (within)  {stats.sigma_within:.5f}   from R-bar / d2",
        f"  sigma (overall) {stats.sigma_overall:.5f}   sample standard deviation",
    ]

    if capability is not None:
        lines += [
            "",
            "Capability",
            f"  Spec limits     {capability.lsl} .. {capability.usl}",
            f"  Cp  {capability.cp:6.3f}      Cpk {capability.cpk:6.3f}",
            f"  Pp  {capability.pp:6.3f}      Ppk {capability.ppk:6.3f}",
            f"  Verdict         Cpk {capability.cpk:.2f} - {_verdict(capability.cpk)}",
        ]
        if capability.cp - capability.pp > 0.1:
            lines.append(
                "  Note            Cp sits above Pp, so more of the variation is "
                "between subgroups than inside them. Look for shifts and drift "
                "over time rather than for spread within a single sample."
            )

    lines += ["", "Nelson rules"]
    if not violations:
        lines.append("  No rule triggered.")
    else:
        for violation in violations:
            points = ", ".join(str(i + 1) for i in violation.indices)
            lines.append(f"  Rule {violation.rule}: {violation.description}")
            lines.append(f"    subgroups {points}")

    return "\n".join(lines) + "\n"
