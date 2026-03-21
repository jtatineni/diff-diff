# Test Data Fixtures

## hrs_edid_validation.csv

**Source:** Dobkin, C., Finkelstein, A., Kluender, R., & Notowidigdo, M. J. (2018).
"The Economic Consequences of Hospital Admissions." *American Economic Review*, 108(2), 308-352.
Replication kit: https://www.openicpsr.org/openicpsr/project/116186/version/V1/view

**Sample selection:** Follows Sun & Abraham (2021), as used by Chen, Sant'Anna & Xie (2025)
Section 6:

1. Read `HRS_long.dta` from the Dobkin et al. replication kit
2. Keep waves 7-11, retain only individuals present in all 5 waves
3. Filter to ever-hospitalized individuals with `first_hosp >= 8`
4. Filter to ages 50-59 at hospitalization (`age_hosp`)
5. Drop wave 11 (no valid comparison group)
6. Recode `first_hosp == 11` as never-treated (`inf`)

**Expected counts:**

| Column | Values |
|--------|--------|
| Total individuals | 656 |
| Waves | 7, 8, 9, 10 |
| Rows | 2,624 |
| G=8 | 252 |
| G=9 | 176 |
| G=10 | 163 |
| G=inf | 65 |

**Columns:** `unit` (hhidpn), `time` (wave), `outcome` (oop_spend, 2005 dollars), `first_treat` (first_hosp)

**Regeneration:** Requires the Dobkin et al. replication kit (`.gitignore`d as `replication_data/`).
The extraction logic is documented in the plan file and was executed as a one-time preprocessing step.
