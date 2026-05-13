# ODK Analysis Pipeline

This repository downloads submission data from ODK Central and stores it as CSV files under `data/` for downstream analysis.

## Current ODK Download

The working download script is:

```powershell
python scripts\download_odk.py
```

It currently downloads the following ODK Central forms:

| Project | Form ID | Output |
| --- | --- | --- |
| `5` | `SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Adolescents)_v1_0` | `data/SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Adolescents)_v1_0.csv` |
| `5` | `SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Caregiver)_v1_0` | `data/SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Caregiver)_v1_0.csv` |
| `5` | `SMART_STEP_9_Month_Endpoint_Assessment_Pack_(Adolescents)_v1_0` | `data/SMART_STEP_9_Month_Endpoint_Assessment_Pack_(Adolescents)_v1_0.csv` |
| `5` | `SMART_STEP_9_Month_Endpoint_Assessment_Pack_(Caregiver)_v1_0` | `data/SMART_STEP_9_Month_Endpoint_Assessment_Pack_(Caregiver)_v1_0.csv` |

The downloader now reads credentials from either:

- PowerShell environment variables in the current shell, or
- a local repo-root `.env` file

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

You can also place the same values in a local `.env` file at the repository root:

```text
ODK_URL=https://gihd.csproject.org
ODK_EMAIL=your-email
ODK_PASSWORD=your-password
```

The `.env` file is ignored by git.

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

To run a specific form explicitly:

```powershell
python scripts\analysis_descriptives.py --data-file "data\SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Caregiver)_v1_0.csv" --form-label 6_month_follow_up_caregiver
```

Outputs:

- `output/<form_label>_descriptives_continuous.csv`
- `output/<form_label>_descriptives_categorical.csv`
- `output/<form_label>_descriptives_missing_variables.csv`
- `output/<form_label>_descriptives_summary.txt`

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

For caregiver forms, the descriptive analysis uses this profile:

- Overall:
  - `srq_-srq_total`
  - `apq_-dsm5_total`
  - `bbscq_-bbscq_total`
  - `cgas_-cgas_response`
- Domain wise:
  - `SRQ`: `srq_-srq_total`, `srq_-srq_total_cat`
  - `APQ`: `apq_-dsm5_total`, `apq_-dsm5_total_cat`
  - `BBSCQ`: `bbscq_-bbscq_total`, `bbscq_-bbscq_relation`, `bbscq_-bbscq_belonging`, `bbscq_-bbscq_comitment`, `bbscq_-bbscq_participation`

Generated caregiver variables:

- `srq_-srq_total_cat`
- `apq_-dsm5_total_cat`

The caregiver descriptive outputs are grouped by:

- `group`
- `gender`
- `new_group`

The current caregiver implementation covers descriptive analysis only. Reliability and group-wise t-tests remain adolescent-only until caregiver-specific specifications are added.

## Reliability Analysis

Run:

```powershell
python scripts\analysis_reliability.py
```

Output:

```text
output/<form_label>_reliability_cronbach_alpha.csv
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
output/<form_label>_groupwise_t_tests.csv
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

## Multi-Form Analysis

Run all configured forms through the current analysis pipeline:

```powershell
python scripts\analysis.py
```

Current behavior:

- adolescent forms run descriptives, reliability, and group-wise t-tests
- caregiver forms run descriptives only
- each output file is tagged with `form_label` and `source_file`
- outputs are written separately per form and do not overwrite each other
- the pipeline generates both:
  - `output/consolidated_report.txt`
  - `output/consolidated_report.docx`

## Consolidated Report

The end-of-pipeline report step generates:

- `output/consolidated_report.txt`: plain-text APA-style tables and narratives
- `output/consolidated_report.docx`: Word version of the same consolidated report

The DOCX report is intended for direct review and editing in Word after the CSV outputs are generated.

## GitHub Actions

The workflow at `.github/workflows/odk_download.yml` is configured to run the pipeline daily and manually through `workflow_dispatch`.

Current schedule:

- every day at `2:00 AM UTC`

The workflow currently runs:

- `python scripts/download_odk.py`
- `python scripts/analysis.py`

It then commits updated files from:

- `data/`
- `output/`

It expects the following GitHub repository secrets:

- `ODK_URL`
- `ODK_EMAIL`
- `ODK_PASSWORD`
