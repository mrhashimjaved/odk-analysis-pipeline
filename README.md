# ODK Analysis Pipeline

This repository downloads submission data from ODK Central and stores it as CSV files under `data/` for downstream analysis.

## Current ODK Download

The working download script is:

```powershell
python scripts\download_odk.py
```

It currently downloads the following ODK Central form:

| Project | Form ID | Output |
| --- | --- | --- |
| `5` | `SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Adolescents)_v1_0` | `data/SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Adolescents)_v1_0.csv` |

The latest verified download produced a valid CSV of about `749 KB` with `593` data rows.

## Required Environment Variables

Set these variables in the same PowerShell session before running the download:

```powershell
$env:ODK_URL="https://your-odk-central-server"
$env:ODK_EMAIL="your-email"
$env:ODK_PASSWORD="your-password"
```

Then run:

```powershell
python scripts\download_odk.py
```

Do not commit credentials to this repository.

## ODK Endpoint Notes

The script uses the ODK Central CSV export endpoint:

```text
/v1/projects/{projectId}/forms/{xmlFormId}/submissions.csv
```

The OData endpoint, `.svc/Submissions`, is not the correct route for direct CSV export in this pipeline.

If a form download returns `404`, the script prints the available forms in the configured project. Check that the project ID and XML form ID match the ODK Central form exactly.

## School Group Reference

The school group lookup file is:

```text
data/school_group_reference.csv
```

It contains `40` schools with these columns:

- `school_id`
- `school_name`
- `group`

The current reference has `20` schools in Group `A` and `20` schools in Group `B`.

The analysis scripts use this file to add:

- `group`: intervention group `A` or `B`
- `gender`: inferred from school ID prefix, where `B` = Boys and `G` = Girls
- `new_group`: combined group and gender labels such as `A_Boys` and `B_Girls`

## Descriptive Analysis

Run:

```powershell
python scripts\analysis_descriptives.py
```

Outputs:

- `output/descriptives_continuous.csv`
- `output/descriptives_categorical.csv`
- `output/descriptives_missing_variables.csv`
- `output/descriptives_summary.txt`

The descriptive script reports:

- continuous variables: `N`, `Mean`, `SD`, `Min-Max`
- categorical variables ending in `_cat` or `_cat_bin`: `N`, `Freq`, `Percentage`
- `cgas_-cgas_response` as categorical
- text summary sections for:
  - Descriptive Statistics of Outcome variables (Overall)
  - Descriptive Statistics of Outcome variables (Domain wise)

Generated PHQ9 variables:

- `phq9a_-phq9a_total_cat_bin`
- `phq9a_-phq9a_total_cat`

## Reliability Analysis

Run:

```powershell
python scripts\analysis_reliability.py
```

Output:

```text
output/reliability_cronbach_alpha.csv
```

The reliability script calculates Cronbach alpha for the configured outcome measures and writes:

- `outcome_measure`
- `total_score_variable`
- `number_of_items`
- `n_complete_cases`
- `cronbach_alpha`
- `missing_items`

Currently configured measures:

- PHQ9
- PSC
- RCADS
- DSM-5
- Somatic
- WEMWBS
- SPSI
- IBS
- BBSCQ
- Self Stigma
- Psychlops-Post

## Group-Wise T-Tests

Run:

```powershell
python scripts\analysis_groupwise_t_tests.py
```

Output:

```text
output/groupwise_t_tests.csv
```

The t-test script compares Group `A` vs Group `B`.

It reports Welch's independent samples t-test as the primary test and Student's equal-variance t-test for comparison.

It writes:

- `variable`
- `group_a_n`
- `group_a_mean`
- `group_a_sd`
- `group_b_n`
- `group_b_mean`
- `group_b_sd`
- `mean_difference`
- `t_statistic`
- `degrees_of_freedom`
- `p_value`
- `significant_0_05`
- `student_t_statistic`
- `student_degrees_of_freedom`
- `student_p_value`
- `student_significant_0_05`

Currently configured t-test variables:

- `phq9a_-phq9a_total`
- `psc_-psc_total`
- `rcads_-rcads_total`
- `dsm5_-dsm5_total`
- `somatic_-somatic_total`
- `wemwbs_-wemwbs_total`
- `ibs_-ibs_total`
- `bbscq_-bbscq_total`
- `self_stigma_-stgt_total`
- `psychlops_post_-psy_total`

## Legacy Analysis

The existing R analysis script is:

```powershell
Rscript scripts\analysis.R
```

At the moment, `scripts/analysis.R` expects `data/your_combined_data.csv`, so it must be updated or given a combined input file before the analysis step will run successfully.

## GitHub Actions

The workflow at `.github/workflows/odk_download.yml` is configured to run the pipeline weekly and manually through `workflow_dispatch`.

Current schedule:

- every Sunday at `2:00 AM UTC`

The workflow currently runs:

- `python scripts/download_odk.py`
- `python scripts/analysis_descriptives.py`
- `python scripts/analysis_reliability.py`
- `python scripts/analysis_groupwise_t_tests.py`

It then commits updated files from:

- `data/`
- `output/`

It expects the following GitHub repository secrets:

- `ODK_URL`
- `ODK_EMAIL`
- `ODK_PASSWORD`
