import csv
import os
from collections import defaultdict

from form_registry import FORMS


OUTPUT_DIR = "output"
REPORT_FILE = os.path.join(OUTPUT_DIR, "consolidated_report.txt")

DESCRIPTIVE_CONTINUOUS_SUFFIX = "_descriptives_continuous.csv"
DESCRIPTIVE_CATEGORICAL_SUFFIX = "_descriptives_categorical.csv"
RELIABILITY_SUFFIX = "_reliability_cronbach_alpha.csv"
TTEST_SUFFIX = "_groupwise_t_tests.csv"


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def form_title(form_config):
    label = form_config["label"]
    parts = label.split("_")
    wave = " ".join(parts[:3]).replace("month", "Month").replace("endpoint", "Endpoint")
    respondent = "Adolescents" if form_config.get("respondent") == "adolescent" else "Caregivers"
    return f"{wave.title()} {respondent}"


def section_title(form_config):
    if form_config.get("respondent") == "adolescent":
        return "Descriptive Statistics (Adolescents)"
    if "domain" in form_config["label"]:
        return "Descriptive Statistics (Caregivers Domain-wise)"
    return "Descriptive Statistics (Caregivers Overall)"


def parse_float(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def format_mean_sd_range(row):
    mean = row.get("mean", "")
    sd = row.get("sd", "")
    min_value = row.get("min", "")
    max_value = row.get("max", "")
    return f"{mean} [{sd}] - {min_value}-{max_value}"


def format_freq_percentage(row):
    return f"{row.get('freq', '')} ({row.get('percentage', '')})"


def reliability_note(alpha_value):
    alpha = parse_float(alpha_value)
    if alpha is None:
        return "not estimated"
    if alpha >= 0.80:
        return "good"
    if alpha >= 0.70:
        return "acceptable"
    if alpha >= 0.60:
        return "borderline"
    return "low"


def significance_note(flag):
    return "significant" if flag == "Yes" else "non-significant"


def load_optional_csv(path):
    return read_csv(path) if os.path.exists(path) else []


def group_rows(rows, *keys):
    grouped = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(key, "") for key in keys)].append(row)
    return grouped


def write_heading(lines, title):
    lines.append(title)
    lines.append("=" * len(title))
    lines.append("")


def write_subheading(lines, title):
    lines.append(title)
    lines.append("-" * len(title))


def describe_descriptives(lines, form_config, continuous_rows, categorical_rows):
    label = form_config["label"]
    title = form_title(form_config)
    lines.append(title)
    lines.append("")
    lines.append(section_title(form_config))
    lines.append("")

    continuous_rows = [row for row in continuous_rows if row.get("group_by") in {"overall", "group", "gender", "new_group"}]
    categorical_rows = [row for row in categorical_rows if row.get("group_by") in {"overall", "group", "gender", "new_group"}]

    continuous_by_scope = group_rows(continuous_rows, "analysis_set", "group_by")
    for analysis_set in ["Overall", "Domain wise"]:
        for group_by in ["overall", "group", "gender", "new_group"]:
            rows = continuous_by_scope.get((analysis_set, group_by), [])
            if not rows:
                continue
            write_subheading(lines, f"{analysis_set} Continuous ({group_by})")
            lines.append("Variable | Summary")
            lines.append("--- | ---")
            for row in rows:
                lines.append(f"{row['variable']} | {format_mean_sd_range(row)}")
            lines.append("")
            lines.append(
                f"In the {label} dataset, continuous outcomes for {analysis_set.lower()} analyses were summarised by {group_by}. "
                f"The table above provides N, mean, standard deviation, and range in compact APA style."
            )
            lines.append("")

    categorical_by_scope = group_rows(categorical_rows, "analysis_set", "group_by", "variable")
    for (analysis_set, group_by, variable), rows in categorical_by_scope.items():
        write_subheading(lines, f"{analysis_set} Categorical ({group_by}) - {variable}")
        lines.append("Category | Summary")
        lines.append("--- | ---")
        for row in rows:
            lines.append(f"{row['category']} | {format_freq_percentage(row)}")
        lines.append("")
        lines.append(
            f"For {variable} in the {label} dataset, the table above shows category frequencies and percentages for the {group_by} breakdown."
        )
        lines.append("")


def describe_reliability(lines, all_rows):
    if not all_rows:
        return
    lines.append("Reliability (Cronbach's Alpha)")
    lines.append("")
    lines.append("Form | Outcome Measure | Variable | Items | N | Alpha | Interpretation")
    lines.append("--- | --- | --- | --- | --- | --- | ---")
    for row in all_rows:
        lines.append(
            f"{row['form_label']} | {row['outcome_measure']} | {row['total_score_variable']} | "
            f"{row['number_of_items']} | {row['n_complete_cases']} | {row['cronbach_alpha']} | {reliability_note(row['cronbach_alpha'])}"
        )
    lines.append("")
    good = [row["outcome_measure"] for row in all_rows if reliability_note(row["cronbach_alpha"]) in {"good", "acceptable"}]
    borderline = [row["outcome_measure"] for row in all_rows if reliability_note(row["cronbach_alpha"]) == "borderline"]
    lines.append(
        "Reliability estimates are presented above for the available adolescent scales. "
        f"Scales in the acceptable-to-good range included: {', '.join(good) if good else 'none'}. "
        f"Borderline scales included: {', '.join(borderline) if borderline else 'none'}."
    )
    lines.append("")


def describe_ttests(lines, all_rows):
    if not all_rows:
        return
    lines.append("Group-wise Welch's and Student's t-tests")
    lines.append("")
    lines.append(
        "Form | Variable | Group A Mean [SD] | Group B Mean [SD] | Mean Difference | "
        "Welch's t(df) | Welch's p | Welch's significance | Student's t(df) | Student's p | Student's significance"
    )
    lines.append("--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---")
    for row in all_rows:
        group_a = f"{row['group_a_mean']} [{row['group_a_sd']}]"
        group_b = f"{row['group_b_mean']} [{row['group_b_sd']}]"
        welch = f"{row['t_statistic']} ({row['degrees_of_freedom']})"
        student = f"{row['student_t_statistic']} ({row['student_degrees_of_freedom']})"
        lines.append(
            f"{row['form_label']} | {row['variable']} | {group_a} | {group_b} | {row['mean_difference']} | "
            f"{welch} | {row['p_value']} | {significance_note(row['significant_0_05'])} | "
            f"{student} | {row['student_p_value']} | {significance_note(row['student_significant_0_05'])}"
        )
    lines.append("")
    significant = [row["variable"] for row in all_rows if row["significant_0_05"] == "Yes"]
    lines.append(
        "The group-wise comparisons above present Welch's and Student's t-tests side by side. "
        f"Outcomes with statistically significant Welch tests were: {', '.join(significant) if significant else 'none'}."
    )
    lines.append("")


def build_report_lines():
    lines = []
    write_heading(lines, "Consolidated APA-Style Results Report")
    lines.append("This report compiles the analysis CSV outputs into plain-text sections for direct pasting into Word.")
    lines.append("")

    reliability_rows = []
    ttest_rows = []

    for form_config in FORMS:
        label = form_config["label"]
        continuous_path = os.path.join(OUTPUT_DIR, f"{label}{DESCRIPTIVE_CONTINUOUS_SUFFIX}")
        categorical_path = os.path.join(OUTPUT_DIR, f"{label}{DESCRIPTIVE_CATEGORICAL_SUFFIX}")
        if os.path.exists(continuous_path) and os.path.exists(categorical_path):
            describe_descriptives(lines, form_config, read_csv(continuous_path), read_csv(categorical_path))

        reliability_path = os.path.join(OUTPUT_DIR, f"{label}{RELIABILITY_SUFFIX}")
        ttest_path = os.path.join(OUTPUT_DIR, f"{label}{TTEST_SUFFIX}")
        reliability_rows.extend(load_optional_csv(reliability_path))
        ttest_rows.extend(load_optional_csv(ttest_path))

    describe_reliability(lines, reliability_rows)
    describe_ttests(lines, ttest_rows)
    return lines


def write_report_file(lines, path=REPORT_FILE):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines).rstrip() + "\n")


def main():
    lines = build_report_lines()
    write_report_file(lines, REPORT_FILE)
    print(f"Wrote {REPORT_FILE}")


if __name__ == "__main__":
    main()
