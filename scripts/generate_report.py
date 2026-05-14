import csv
import os
from collections import defaultdict

from form_registry import FORMS
from new_gp_loader import NEW_GP_LABELS, NEW_GP_ORDER, NEW_GP_PAIRS


OUTPUT_DIR = "output"
REPORT_FILE = os.path.join(OUTPUT_DIR, "consolidated_report.txt")

DESCRIPTIVE_CONTINUOUS_SUFFIX = "_descriptives_continuous.csv"
DESCRIPTIVE_CATEGORICAL_SUFFIX = "_descriptives_categorical.csv"
RELIABILITY_SUFFIX = "_reliability_cronbach_alpha.csv"
TTEST_SUFFIX = "_groupwise_t_tests.csv"
NEW_GP_TTEST_SUFFIX = "_new_gp_t_tests.csv"
NEW_GP_RELIABILITY_SUFFIX = "_new_gp_reliability_cronbach_alpha.csv"


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def load_optional_csv(path):
    return read_csv(path) if os.path.exists(path) else []


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


# ── DESCRIPTIVES ──────────────────────────────────────────────────────────────

def describe_descriptives(lines, form_config, continuous_rows, categorical_rows):
    label = form_config["label"]
    lines.append(form_title(form_config))
    lines.append("")
    lines.append(section_title(form_config))
    lines.append("")

    standard_group_bys = {"overall", "group", "gender", "new_group"}
    cont_standard = [r for r in continuous_rows if r.get("group_by") in standard_group_bys]
    cat_standard = [r for r in categorical_rows if r.get("group_by") in standard_group_bys]

    continuous_by_scope = group_rows(cont_standard, "analysis_set", "group_by")
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
                f"In the {label} dataset, continuous outcomes for {analysis_set.lower()} analyses "
                f"were summarised by {group_by}. "
                "The table above provides N, mean, standard deviation, and range in compact APA style."
            )
            lines.append("")

    categorical_by_scope = group_rows(cat_standard, "analysis_set", "group_by", "variable")
    for (analysis_set, group_by, variable), rows in categorical_by_scope.items():
        write_subheading(lines, f"{analysis_set} Categorical ({group_by}) - {variable}")
        lines.append("Category | Summary")
        lines.append("--- | ---")
        for row in rows:
            lines.append(f"{row['category']} | {format_freq_percentage(row)}")
        lines.append("")
        lines.append(
            f"For {variable} in the {label} dataset, the table above shows category "
            f"frequencies and percentages for the {group_by} breakdown."
        )
        lines.append("")


def describe_new_gp_descriptives(lines, form_config, continuous_rows, categorical_rows):
    """Write descriptive tables broken down by New_GP group."""
    label = form_config["label"]
    cont_gp = [r for r in continuous_rows if r.get("group_by") == "new_gp"]
    cat_gp = [r for r in categorical_rows if r.get("group_by") == "new_gp"]
    if not cont_gp and not cat_gp:
        return

    write_subheading(lines, f"New_GP Group Descriptives — {form_title(form_config)}")
    lines.append("")

    continuous_by_scope = group_rows(cont_gp, "analysis_set")
    for analysis_set in ["Overall", "Domain wise"]:
        rows = continuous_by_scope.get((analysis_set,), [])
        if not rows:
            continue
        write_subheading(lines, f"{analysis_set} Continuous by New_GP Group")
        # Dynamic header: Variable + one column per new_gp value present
        gp_values = sorted({r["group_value"] for r in rows})
        lines.append("Variable | " + " | ".join(gp_values))
        lines.append("--- | " + " | ".join(["---"] * len(gp_values)))
        variables = list(dict.fromkeys(r["variable"] for r in rows))
        for variable in variables:
            var_rows = {r["group_value"]: r for r in rows if r["variable"] == variable}
            cells = [format_mean_sd_range(var_rows[gv]) if gv in var_rows else "" for gv in gp_values]
            lines.append(f"{variable} | " + " | ".join(cells))
        lines.append("")

    cat_by_scope = group_rows(cat_gp, "analysis_set", "variable")
    for (analysis_set, variable), rows in cat_by_scope.items():
        gp_values = sorted({r["group_value"] for r in rows})
        categories = list(dict.fromkeys(r["category"] for r in rows))
        write_subheading(lines, f"{analysis_set} Categorical by New_GP — {variable}")
        lines.append("Category | " + " | ".join(gp_values))
        lines.append("--- | " + " | ".join(["---"] * len(gp_values)))
        for cat in categories:
            cat_rows = {r["group_value"]: r for r in rows if r["category"] == cat}
            cells = [format_freq_percentage(cat_rows[gv]) if gv in cat_rows else "" for gv in gp_values]
            lines.append(f"{cat} | " + " | ".join(cells))
        lines.append("")


# ── RELIABILITY ───────────────────────────────────────────────────────────────

def describe_reliability(lines, all_rows):
    if not all_rows:
        return
    lines.append("Reliability (Cronbach's Alpha) — Overall")
    lines.append("")
    lines.append("Form | Outcome Measure | Variable | Items | N | Alpha | Interpretation")
    lines.append("--- | --- | --- | --- | --- | --- | ---")
    for row in all_rows:
        lines.append(
            f"{row['form_label']} | {row['outcome_measure']} | {row['total_score_variable']} | "
            f"{row['number_of_items']} | {row['n_complete_cases']} | {row['cronbach_alpha']} | "
            f"{reliability_note(row['cronbach_alpha'])}"
        )
    lines.append("")
    good = [r["outcome_measure"] for r in all_rows if reliability_note(r["cronbach_alpha"]) in {"good", "acceptable"}]
    borderline = [r["outcome_measure"] for r in all_rows if reliability_note(r["cronbach_alpha"]) == "borderline"]
    lines.append(
        "Reliability estimates are presented above for the available scales. "
        f"Scales in the acceptable-to-good range: {', '.join(good) if good else 'none'}. "
        f"Borderline scales: {', '.join(borderline) if borderline else 'none'}."
    )
    lines.append("")


def describe_new_gp_reliability(lines, all_rows):
    if not all_rows:
        return
    lines.append("Reliability (Cronbach's Alpha) by New_GP Group")
    lines.append("")
    lines.append("Form | New_GP Group | N | Outcome Measure | Items | n Complete | Alpha | Interpretation")
    lines.append("--- | --- | --- | --- | --- | --- | --- | ---")
    for row in all_rows:
        lines.append(
            f"{row['form_label']} | {row['new_gp_group']} | {row['new_gp_n']} | "
            f"{row['outcome_measure']} | {row['number_of_items']} | "
            f"{row['n_complete_cases']} | {row['cronbach_alpha']} | "
            f"{reliability_note(row['cronbach_alpha'])}"
        )
    lines.append("")


# ── T-TESTS ───────────────────────────────────────────────────────────────────

def describe_ttests(lines, all_rows):
    if not all_rows:
        return
    lines.append("Group-wise Welch's and Student's t-tests (Group A vs Group B)")
    lines.append("")
    lines.append(
        "Form | Variable | Group A Mean [SD] | Group B Mean [SD] | Mean Difference | "
        "Welch's t(df) | Welch's p | Welch's sig | Student's t(df) | Student's p | Student's sig"
    )
    lines.append("--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---")
    for row in all_rows:
        group_a = f"{row['group_a_mean']} [{row['group_a_sd']}]"
        group_b = f"{row['group_b_mean']} [{row['group_b_sd']}]"
        welch = f"{row['t_statistic']} ({row['degrees_of_freedom']})"
        student = f"{row['student_t_statistic']} ({row['student_degrees_of_freedom']})"
        lines.append(
            f"{row['form_label']} | {row['variable']} | {group_a} | {group_b} | "
            f"{row['mean_difference']} | {welch} | {row['p_value']} | "
            f"{significance_note(row['significant_0_05'])} | "
            f"{student} | {row['student_p_value']} | "
            f"{significance_note(row['student_significant_0_05'])}"
        )
    lines.append("")
    significant = [r["variable"] for r in all_rows if r["significant_0_05"] == "Yes"]
    lines.append(
        "The group-wise comparisons above present Welch's and Student's t-tests side by side. "
        f"Outcomes with statistically significant Welch tests: {', '.join(significant) if significant else 'none'}."
    )
    lines.append("")


def describe_new_gp_ttests(lines, all_rows):
    """Write New_GP pairwise t-test tables, one comparison block per variable."""
    if not all_rows:
        return
    lines.append("New_GP Pairwise t-tests (All 15 Group Combinations)")
    lines.append("")

    variables = list(dict.fromkeys(r["variable"] for r in all_rows))
    for variable in variables:
        var_rows = [r for r in all_rows if r["variable"] == variable]
        write_subheading(lines, f"Variable: {variable}")
        lines.append(
            "Form | Comparison | Group 1 Label | Group 1 N | Group 1 Mean [SD] | "
            "Group 2 Label | Group 2 N | Group 2 Mean [SD] | Mean Diff | "
            "Welch t(df) | p | Sig | Student t(df) | p | Sig"
        )
        lines.append("--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---")
        for row in var_rows:
            g1 = f"{row['group_1_mean']} [{row['group_1_sd']}]"
            g2 = f"{row['group_2_mean']} [{row['group_2_sd']}]"
            welch = f"{row['t_statistic']} ({row['degrees_of_freedom']})"
            student = f"{row['student_t_statistic']} ({row['student_degrees_of_freedom']})"
            lines.append(
                f"{row['form_label']} | {row['comparison']} | {row['group_1_label']} | "
                f"{row['group_1_n']} | {g1} | {row['group_2_label']} | {row['group_2_n']} | "
                f"{g2} | {row['mean_difference']} | {welch} | {row['p_value']} | "
                f"{significance_note(row['significant_0_05'])} | {student} | "
                f"{row['student_p_value']} | {significance_note(row['student_significant_0_05'])}"
            )
        sig_pairs = [r["comparison"] for r in var_rows if r["significant_0_05"] == "Yes"]
        lines.append("")
        lines.append(
            f"Significant pairwise comparisons for {variable}: "
            f"{', '.join(sig_pairs) if sig_pairs else 'none'}."
        )
        lines.append("")


# ── REPORT BUILDER ────────────────────────────────────────────────────────────

def forms_for_time_point(time_point):
    """Filter FORMS by time point prefix: '6_month' or '9_month'."""
    if time_point is None:
        return FORMS
    return [f for f in FORMS if f["label"].startswith(time_point)]


def build_report_lines(time_point=None):
    """
    Build report lines for the given time_point ('6_month', '9_month', or None for all).
    """
    forms = forms_for_time_point(time_point)
    lines = []

    if time_point == "6_month":
        title = "6-Month Follow-Up Results Report"
    elif time_point == "9_month":
        title = "9-Month Endpoint Results Report"
    else:
        title = "Consolidated APA-Style Results Report"

    write_heading(lines, title)
    lines.append("This report compiles the analysis CSV outputs into plain-text sections.")
    lines.append("")

    # ── Descriptive statistics ────────────────────────────────────────────────
    write_heading(lines, "Section 1: Descriptive Statistics")
    for form_config in forms:
        label = form_config["label"]
        continuous_path = os.path.join(OUTPUT_DIR, f"{label}{DESCRIPTIVE_CONTINUOUS_SUFFIX}")
        categorical_path = os.path.join(OUTPUT_DIR, f"{label}{DESCRIPTIVE_CATEGORICAL_SUFFIX}")
        if os.path.exists(continuous_path) and os.path.exists(categorical_path):
            cont = read_csv(continuous_path)
            cat = read_csv(categorical_path)
            describe_descriptives(lines, form_config, cont, cat)

    # ── New_GP descriptives ───────────────────────────────────────────────────
    has_new_gp_desc = False
    for form_config in forms:
        label = form_config["label"]
        continuous_path = os.path.join(OUTPUT_DIR, f"{label}{DESCRIPTIVE_CONTINUOUS_SUFFIX}")
        categorical_path = os.path.join(OUTPUT_DIR, f"{label}{DESCRIPTIVE_CATEGORICAL_SUFFIX}")
        if os.path.exists(continuous_path) and os.path.exists(categorical_path):
            cont = read_csv(continuous_path)
            cat = read_csv(categorical_path)
            cont_gp = [r for r in cont if r.get("group_by") == "new_gp"]
            cat_gp = [r for r in cat if r.get("group_by") == "new_gp"]
            if cont_gp or cat_gp:
                if not has_new_gp_desc:
                    write_heading(lines, "Section 2: New_GP Group Descriptives")
                    has_new_gp_desc = True
                describe_new_gp_descriptives(lines, form_config, cont, cat)

    # ── Reliability overall ───────────────────────────────────────────────────
    write_heading(lines, "Section 3: Reliability (Cronbach's Alpha)")
    reliability_rows = []
    for form_config in forms:
        label = form_config["label"]
        path = os.path.join(OUTPUT_DIR, f"{label}{RELIABILITY_SUFFIX}")
        reliability_rows.extend(load_optional_csv(path))
    describe_reliability(lines, reliability_rows)

    # ── New_GP reliability ────────────────────────────────────────────────────
    new_gp_reliability_rows = []
    for form_config in forms:
        label = form_config["label"]
        path = os.path.join(OUTPUT_DIR, f"{label}{NEW_GP_RELIABILITY_SUFFIX}")
        new_gp_reliability_rows.extend(load_optional_csv(path))
    if new_gp_reliability_rows:
        write_heading(lines, "Section 4: New_GP Reliability")
        describe_new_gp_reliability(lines, new_gp_reliability_rows)

    # ── Group A vs B t-tests ──────────────────────────────────────────────────
    write_heading(lines, "Section 5: Group A vs Group B t-tests")
    ttest_rows = []
    for form_config in forms:
        label = form_config["label"]
        path = os.path.join(OUTPUT_DIR, f"{label}{TTEST_SUFFIX}")
        ttest_rows.extend(load_optional_csv(path))
    describe_ttests(lines, ttest_rows)

    # ── New_GP pairwise t-tests ───────────────────────────────────────────────
    new_gp_ttest_rows = []
    for form_config in forms:
        label = form_config["label"]
        path = os.path.join(OUTPUT_DIR, f"{label}{NEW_GP_TTEST_SUFFIX}")
        new_gp_ttest_rows.extend(load_optional_csv(path))
    if new_gp_ttest_rows:
        write_heading(lines, "Section 6: New_GP Pairwise t-tests")
        describe_new_gp_ttests(lines, new_gp_ttest_rows)

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
