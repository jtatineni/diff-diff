"""
Validation tests for EfficientDiD against Chen, Sant'Anna & Xie (2025).

Path 1: HRS empirical replication (Table 6 of the paper)
Path 2: Compustat MC simulations (Tables 4 & 5 patterns)

These tests validate the estimator against published results from
"Efficient Difference-in-Differences and Event Study Estimators."
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from diff_diff import CallawaySantAnna, EfficientDiD

# =============================================================================
# Data Loaders & Helpers
# =============================================================================

_HRS_FIXTURE = Path(__file__).parent / "data" / "hrs_edid_validation.csv"

# Paper Table 6 reference values: (point_estimate, cluster_robust_se)
TABLE6_EDID = {
    (8, 8): (3072, 806),
    (8, 9): (1112, 637),
    (8, 10): (1038, 817),
    (9, 9): (3063, 690),
    (9, 10): (90, 641),
    (10, 10): (2908, 894),
}
TABLE6_ES = {
    0: (3024, 486),
    1: (692, 471),
    2: (1038, 816),
}
TABLE6_ES_AVG = (1585, 521)

TABLE6_CS_SA = {
    (8, 8): 2826,
    (8, 9): 825,
    (8, 10): 800,
    (9, 9): 3031,
    (9, 10): 107,
    (10, 10): 3092,
}


def _load_hrs_data():
    """Load the committed HRS test fixture."""
    df = pd.read_csv(_HRS_FIXTURE)
    # Ensure correct types
    df["unit"] = df["unit"].astype(int)
    df["time"] = df["time"].astype(int)
    df["first_treat"] = df["first_treat"].astype(float)
    return df


def _get_effect(effects_dict, g, t):
    """Look up ATT(g,t) handling potential float/int key mismatch."""
    for key, val in effects_dict.items():
        if int(key[0]) == g and int(key[1]) == t:
            return val
    raise KeyError(f"ATT({g},{t}) not found in results")


def _assert_close(actual, expected, label, rtol=0.10, atol=200):
    """Assert actual is close to expected with combined tolerance."""
    tol = max(rtol * abs(expected), atol)
    diff = abs(actual - expected)
    assert diff < tol, (
        f"{label}: expected {expected}, got {actual:.1f} "
        f"(diff={diff:.1f}, tol={tol:.1f})"
    )


# =============================================================================
# Compustat DGP (copied from test_efficient_did.py)
# =============================================================================


def _make_compustat_dgp(n_units=400, n_periods=11, rho=0.0, seed=42):
    """Simplified Compustat-style DGP from Section 5.2.

    Groups: G=5 (~1/3), G=8 (~1/3), G=inf (~1/3).
    ATT(5,t) = 0.154*(t-4), ATT(8,t) = 0.093*(t-7).
    """
    rng = np.random.default_rng(seed)
    n_t = n_periods

    n_g5 = n_units // 3
    n_g8 = n_units // 3
    ft = np.full(n_units, np.inf)
    ft[:n_g5] = 5
    ft[n_g5 : n_g5 + n_g8] = 8

    units = np.repeat(np.arange(n_units), n_t)
    times = np.tile(np.arange(1, n_t + 1), n_units)
    ft_col = np.repeat(ft, n_t)

    alpha_t = rng.normal(0, 0.1, n_t)
    eta_i = rng.normal(0, 0.5, n_units)
    unit_fe = np.repeat(eta_i, n_t)
    time_fe = np.tile(alpha_t, n_units)

    eps = np.zeros((n_units, n_t))
    eps[:, 0] = rng.normal(0, 0.3, n_units)
    for t in range(1, n_t):
        eps[:, t] = rho * eps[:, t - 1] + rng.normal(0, 0.3, n_units)
    eps_flat = eps.flatten()

    tau = np.zeros(len(units))
    for i in range(n_units):
        g = ft[i]
        if np.isinf(g):
            continue
        for t_idx in range(n_t):
            t = t_idx + 1
            if g == 5 and t >= 5:
                tau[i * n_t + t_idx] = 0.154 * (t - 4)
            elif g == 8 and t >= 8:
                tau[i * n_t + t_idx] = 0.093 * (t - 7)

    y = unit_fe + time_fe + tau + eps_flat

    return pd.DataFrame(
        {"unit": units, "time": times, "first_treat": ft_col, "y": y}
    )


def _compute_es_avg(result):
    """Compute ES_avg (Eq 2.3): uniform average over post-treatment horizons."""
    if result.event_study_effects is None:
        raise ValueError("No event study effects; use aggregate='all'")
    es = {
        int(e): d["effect"]
        for e, d in result.event_study_effects.items()
        if int(e) >= 0
    }
    return np.mean(list(es.values()))


# Ground truth ES_avg for Compustat DGP (see plan for derivation)
_TRUE_ES_AVG_COMPUSTAT = np.mean(
    [0.1235, 0.247, 0.3705, 0.494, 0.770, 0.924, 1.078]
)


def _true_overall_att_compustat():
    """Compute true overall_att using cohort-size weighting (our convention)."""
    # Groups have equal size (1/3 each), so pi_5 = pi_8
    # Post-treatment (g,t) cells:
    # G=5: t=5..11 -> 7 cells with effects 0.154*(1..7)
    # G=8: t=8..11 -> 4 cells with effects 0.093*(1..4)
    effects_g5 = [0.154 * k for k in range(1, 8)]  # 7 cells
    effects_g8 = [0.093 * k for k in range(1, 5)]  # 4 cells
    # Cohort-size-weighted: both groups have same pi, so weight by count
    all_effects = effects_g5 + effects_g8
    return np.mean(all_effects)


def _run_mc_simulation(n_sims, rho, seed=1000, also_cs=False):
    """Run MC simulation and return estimates."""
    edid_estimates = []
    edid_overall_att = []
    edid_overall_ci = []
    edid_overall_se = []
    cs_estimates_list = []

    for i in range(n_sims):
        data = _make_compustat_dgp(rho=rho, seed=seed + i)

        edid = EfficientDiD(pt_assumption="all")
        res = edid.fit(
            data, outcome="y", unit="unit", time="time",
            first_treat="first_treat", aggregate="all",
        )
        edid_estimates.append(_compute_es_avg(res))
        edid_overall_att.append(res.overall_att)
        edid_overall_se.append(res.overall_se)
        edid_overall_ci.append(res.overall_conf_int)

        if also_cs:
            cs = CallawaySantAnna(control_group="never_treated")
            cs_res = cs.fit(
                data, outcome="y", unit="unit", time="time",
                first_treat="first_treat", aggregate="event_study",
            )
            cs_estimates_list.append(_compute_es_avg(cs_res))

    return {
        "edid_estimates": np.array(edid_estimates),
        "edid_overall_att": np.array(edid_overall_att),
        "edid_overall_se": np.array(edid_overall_se),
        "edid_overall_ci": np.array(edid_overall_ci),
        "cs_estimates": np.array(cs_estimates_list) if also_cs else None,
    }


# =============================================================================
# Path 1: HRS Empirical Replication (Table 6)
# =============================================================================


@pytest.fixture(scope="module")
def hrs_data():
    """Load HRS validation fixture."""
    if not _HRS_FIXTURE.exists():
        pytest.skip(f"HRS fixture not found at {_HRS_FIXTURE}")
    return _load_hrs_data()


@pytest.fixture(scope="module")
def edid_hrs_result(hrs_data):
    """Fit EDiD on HRS data (shared across tests)."""
    edid = EfficientDiD(pt_assumption="all")
    return edid.fit(
        hrs_data, outcome="outcome", unit="unit", time="time",
        first_treat="first_treat", aggregate="all",
    )


class TestHRSReplication:
    """Validate EDiD against Table 6 of Chen, Sant'Anna & Xie (2025)."""

    def test_sample_selection_yields_expected_counts(self, hrs_data):
        n_units = hrs_data["unit"].nunique()
        assert abs(n_units - 652) <= 10, f"Expected ~652 units, got {n_units}"

        groups = hrs_data.groupby("unit")["first_treat"].first()

        # Check 4 groups exist
        finite_groups = sorted(g for g in groups.unique() if np.isfinite(g))
        assert finite_groups == [8, 9, 10], f"Expected groups [8,9,10], got {finite_groups}"
        assert any(np.isinf(g) for g in groups.unique()), "Missing never-treated group"

        # Check approximate sizes
        for g, expected in [(8, 252), (9, 176), (10, 163)]:
            actual = (groups == g).sum()
            assert abs(actual - expected) <= 15, (
                f"G={g}: expected ~{expected}, got {actual}"
            )
        n_inf = groups.apply(np.isinf).sum()
        assert abs(n_inf - 65) <= 10, f"G=inf: expected ~65, got {n_inf}"

    def test_group_time_effects_match_table6(self, edid_hrs_result):
        for (g, t), (expected_effect, _) in TABLE6_EDID.items():
            info = _get_effect(edid_hrs_result.group_time_effects, g, t)
            _assert_close(info["effect"], expected_effect, f"ATT({g},{t})")

    def test_event_study_effects_match_table6(self, edid_hrs_result):
        for e, (expected_effect, _) in TABLE6_ES.items():
            # Find event study effect matching relative time e
            found = False
            for rel_time, info in edid_hrs_result.event_study_effects.items():
                if int(rel_time) == e:
                    _assert_close(info["effect"], expected_effect, f"ES({e})")
                    found = True
                    break
            assert found, f"ES({e}) not found in event study effects"

    def test_es_avg_matches_table6(self, edid_hrs_result):
        es_avg = _compute_es_avg(edid_hrs_result)
        _assert_close(es_avg, TABLE6_ES_AVG[0], "ES_avg")

    def test_se_diagnostic_comparison(self, edid_hrs_result):
        """Log and sanity-check analytical vs cluster-robust SEs."""
        for (g, t), (_, cluster_se) in TABLE6_EDID.items():
            info = _get_effect(edid_hrs_result.group_time_effects, g, t)
            analytical_se = info["se"]
            assert np.isfinite(analytical_se) and analytical_se > 0, (
                f"ATT({g},{t}): analytical SE should be finite positive, got {analytical_se}"
            )
            ratio = analytical_se / cluster_se
            assert 0.3 < ratio < 3.0, (
                f"ATT({g},{t}): SE ratio (analytical/cluster) = {ratio:.2f} "
                f"outside (0.3, 3.0). Analytical={analytical_se:.1f}, "
                f"cluster={cluster_se}"
            )

    def test_cs_cross_validation(self, hrs_data):
        """Cross-validate data loading using CallawaySantAnna."""
        cs = CallawaySantAnna(control_group="never_treated")
        cs_result = cs.fit(
            hrs_data, outcome="outcome", unit="unit", time="time",
            first_treat="first_treat",
        )
        for (g, t), expected_effect in TABLE6_CS_SA.items():
            info = _get_effect(cs_result.group_time_effects, g, t)
            _assert_close(
                info["effect"], expected_effect,
                f"CS ATT({g},{t})", rtol=0.15, atol=300,
            )

    def test_pretreatment_effects_near_zero(self, edid_hrs_result):
        """Check pre-treatment effects are small (parallel trends plausibility)."""
        pre_effects = []
        post_effects = []
        for (g, t), info in edid_hrs_result.group_time_effects.items():
            g_int, t_int = int(g), int(t)
            if t_int < g_int:
                pre_effects.append(abs(info["effect"]))
            else:
                post_effects.append(abs(info["effect"]))

        if not pre_effects:
            pytest.skip("No pre-treatment effects to check")

        mean_post = np.mean(post_effects)
        for i, pre_eff in enumerate(pre_effects):
            assert pre_eff < 0.5 * mean_post, (
                f"Pre-treatment effect [{i}] = {pre_eff:.1f} is too large "
                f"relative to mean post-treatment ({mean_post:.1f})"
            )


# =============================================================================
# Path 2: Compustat MC Simulations (Tables 4 & 5 patterns)
# =============================================================================


@pytest.mark.slow
class TestCompustatMCValidation:
    """Validate MC properties against Tables 4 & 5 patterns."""

    @pytest.mark.parametrize("rho", [0, 0.5, -0.5])
    def test_unbiasedness(self, ci_params, rho):
        n_sims = ci_params.bootstrap(200, min_n=49)
        mc = _run_mc_simulation(n_sims, rho=rho, seed=2000 + int(rho * 100))

        mean_est = np.mean(mc["edid_estimates"])
        mcse = np.std(mc["edid_estimates"]) / np.sqrt(n_sims)
        bias = abs(mean_est - _TRUE_ES_AVG_COMPUSTAT)

        assert bias < 3 * mcse + 0.05, (
            f"rho={rho}: bias={bias:.4f}, 3*MCSE={3*mcse:.4f}, "
            f"mean={mean_est:.4f}, true={_TRUE_ES_AVG_COMPUSTAT:.4f}"
        )

    @pytest.mark.parametrize("rho", [0, -0.5])
    def test_edid_has_lower_rmse_than_cs(self, ci_params, rho):
        n_sims = ci_params.bootstrap(150, min_n=49)
        mc = _run_mc_simulation(
            n_sims, rho=rho, seed=3000 + int(rho * 100), also_cs=True,
        )

        rmse_edid = np.sqrt(
            np.mean((mc["edid_estimates"] - _TRUE_ES_AVG_COMPUSTAT) ** 2)
        )
        rmse_cs = np.sqrt(
            np.mean((mc["cs_estimates"] - _TRUE_ES_AVG_COMPUSTAT) ** 2)
        )

        # EDiD should not be meaningfully worse than CS
        assert rmse_edid <= rmse_cs * 1.15, (
            f"rho={rho}: RMSE_edid={rmse_edid:.4f} > RMSE_cs={rmse_cs:.4f} * 1.15"
        )

        # For negative rho, efficiency gain should be clear
        if rho == -0.5:
            assert rmse_edid < rmse_cs, (
                f"rho={rho}: Expected RMSE_edid < RMSE_cs, "
                f"got {rmse_edid:.4f} >= {rmse_cs:.4f}"
            )

    def test_efficiency_gain_increases_with_serial_correlation(self, ci_params):
        n_sims = ci_params.bootstrap(150, min_n=49)
        mc_zero = _run_mc_simulation(n_sims, rho=0, seed=4000, also_cs=True)
        mc_neg = _run_mc_simulation(n_sims, rho=-0.5, seed=4500, also_cs=True)

        def rel_rmse(mc):
            rmse_e = np.sqrt(
                np.mean((mc["edid_estimates"] - _TRUE_ES_AVG_COMPUSTAT) ** 2)
            )
            rmse_c = np.sqrt(
                np.mean((mc["cs_estimates"] - _TRUE_ES_AVG_COMPUSTAT) ** 2)
            )
            return rmse_c / rmse_e if rmse_e > 0 else 1.0

        rel_zero = rel_rmse(mc_zero)
        rel_neg = rel_rmse(mc_neg)

        assert rel_neg > rel_zero, (
            f"Expected larger efficiency gain at rho=-0.5 ({rel_neg:.2f}) "
            f"than rho=0 ({rel_zero:.2f})"
        )

    def test_coverage_approximately_correct(self, ci_params):
        n_sims = ci_params.bootstrap(200, min_n=49)
        mc = _run_mc_simulation(n_sims, rho=0, seed=5000)

        true_overall = _true_overall_att_compustat()
        covered = sum(
            ci[0] <= true_overall <= ci[1]
            for ci in mc["edid_overall_ci"]
        )
        coverage = covered / n_sims

        if n_sims >= 200:
            assert 0.88 <= coverage <= 0.99, (
                f"Coverage={coverage:.2f}, expected 0.88-0.99 (n_sims={n_sims})"
            )
        else:
            assert 0.80 <= coverage <= 1.00, (
                f"Coverage={coverage:.2f}, expected 0.80-1.00 (n_sims={n_sims})"
            )

    def test_analytical_se_calibration(self, ci_params):
        n_sims = ci_params.bootstrap(200, min_n=49)
        mc = _run_mc_simulation(n_sims, rho=0, seed=6000)

        mean_se = np.mean(mc["edid_overall_se"])
        mc_sd = np.std(mc["edid_overall_att"])

        ratio = mean_se / mc_sd if mc_sd > 0 else float("inf")
        assert 0.7 < ratio < 1.4, (
            f"SE calibration ratio={ratio:.2f} (mean_analytical={mean_se:.4f}, "
            f"mc_sd={mc_sd:.4f}), expected 0.7-1.4"
        )
