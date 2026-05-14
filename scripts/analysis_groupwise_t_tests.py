import csv
import math
import os
import argparse
from statistics import mean, stdev, variance

from new_gp_loader import (
    DEFAULT_NEW_GP_FILE,
    NEW_GP_LABELS,
    NEW_GP_PAIRS,
    find_child_id_col,
    load_new_gp_reference,
    apply_new_gp,
)

SCHOOL_REFERENCE_FILE = "data/school_group_reference.csv"
OUTPUT_DIR = "output"
DEFAULT_DATA_FILE = "data/SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Adolescents)_v1_0.csv"
DEFAULT_FORM_LABEL = "6_month_follow_up_adolescents"

GROUPING_VARIABLE = "group"
GROUP_A = "A"
GROUP_B = "B"

# ── OUTCOME VARIABLE LISTS ────────────────────────────────────────────────────
ADOLESCENT_OUTCOME_VARIABLES = [
    "phq9a_-phq9a_total",
    "psc_-psc_total",
    "rcads_-rcads_total",
    "dsm5_-dsm5_total",
    "somatic_-somatic_total",
    "wemwbs_-wemwbs_total",
    "ibs_-ibs_total",
    "bbscq_-bbscq_total",
    "self_stigma_-stgt_total",
    "psychlops_post_-psy_total",
]

CAREGIVER_OUTCOME_VARIABLES = [
    "srq_-srq_total",
    "apq_-dsm5_total",
    "bbscq_-bbscq_total",
    "bbscq_-bbscq_relation",
    "bbscq_-bbscq_belonging",
    "bbscq_-bbscq_comitment",
    "bbscq_-bbscq_participation",
]


def resolve_outcome_variables(form_label):
    if "caregiver" in form_label.lower():
        return CAREGIVER_OUTCOME_VARIABLES
    return ADOLESCENT_OUTCOME_VARIABLES


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def to_float(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    if math.isnan(number):
        return None
    return number


def load_school_reference(path):
    reference = {}
    for row in read_csv(path):
        reference[row["school_id"].strip()] = row["group"].strip()
    return reference


def add_group(row, school_reference):
    school_id = (
        row.get("demo_a_-sch_id") or row.get("demo_b_-csv_sch_id") or ""
    ).strip()
    row[GROUPING_VARIABLE] = school_reference.get(school_id, "")


def format_number(value, digits=4):
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def welch_t_test(group_a_values, group_b_values):
    n_a = len(group_a_values)
    n_b = len(group_b_values)
    if n_a < 2 or n_b < 2:
        return None, None, None

    mean_a = mean(group_a_values)
    mean_b = mean(group_b_values)
    var_a = variance(group_a_values)
    var_b = variance(group_b_values)
    se_squared = (var_a / n_a) + (var_b / n_b)
    if se_squared == 0:
        return None, None, None

    t_statistic = (mean_a - mean_b) / math.sqrt(se_squared)
    numerator = se_squared ** 2
    denominator = (
        (var_a / n_a) ** 2 / (n_a - 1)
    ) + (
        (var_b / n_b) ** 2 / (n_b - 1)
    )
    degrees_of_freedom = numerator / denominator if denominator else None
    p_value = two_tailed_t_p_value(t_statistic, degrees_of_freedom)
    return t_statistic, degrees_of_freedom, p_value


def student_t_test(group_a_values, group_b_values):
    n_a = len(group_a_values)
    n_b = len(group_b_values)
    if n_a < 2 or n_b < 2:
        return None, None, None

    mean_a = mean(group_a_values)
    mean_b = mean(group_b_values)
    var_a = variance(group_a_values)
    var_b = variance(group_b_values)
    degrees_of_freedom = n_a + n_b - 2
    pooled_variance = (
        ((n_a - 1) * var_a) + ((n_b - 1) * var_b)
    ) / degrees_of_freedom
    se = math.sqrt(pooled_variance * ((1 / n_a) + (1 / n_b)))
    if se == 0:
        return None, None, None

    t_statistic = (mean_a - mean_b) / se
    p_value = two_tailed_t_p_value(t_statistic, degrees_of_freedom)
    return t_statistic, degrees_of_freedom, p_value


def two_tailed_t_p_value(t_statistic, degrees_of_freedom):
    if degrees_of_freedom is None:
        return None
    t_abs = abs(t_statistic)
    x = degrees_of_freedom / (degrees_of_freedom + t_abs * t_abs)
    return regularized_incomplete_beta(x, degrees_of_freedom / 2, 0.5)


def regularized_incomplete_beta(x, a, b):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0

    log_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(a * math.log(x) + b * math.log1p(-x) - log_beta)

    if x < (a + 1) / (a + b + 2):
        return front * beta_continued_fraction(x, a, b) / a
    return 1 - front * beta_continued_fraction(1 - x, b, a) / b


def beta_continued_fraction(x, a, b, max_iterations=200, tolerance=3e-14):
    tiny = 1e-300
    qab = a + b
    qap = a + 1
    qam = a - 1
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d

    for m in range(1, max_iterations + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c

        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta

        if abs(delta - 1.0) < tolerance:
            break

    return h


def run_t_tests(values_a, values_b):
    """Return dict with Welch + Student results for two value lists."""
    t_stat, df, p = welch_t_test(values_a, values_b)
    st_stat, st_df, st_p = student_t_test(values_a, values_b)
    mean_a = mean(values_a) if values_a else None
    mean_b = mean(values_b) if values_b else None
    return {
        "group_1_n": len(values_a),
        "group_1_mean": format_number(mean_a),
        "group_1_sd": format_number(stdev(values_a) if len(values_a) > 1 else None),
        "group_2_n": len(values_b),
        "group_2_mean": format_number(mean_b),
        "group_2_sd": format_number(stdev(values_b) if len(values_b) > 1 else None),
        "mean_difference": format_number(
            mean_a - mean_b if mean_a is not None and mean_b is not None else None
        ),
        "t_statistic": format_number(t_stat),
        "degrees_of_freedom": format_number(df),
        "p_value": format_number(p, digits=6),
        "significant_0_05": "Yes" if p is not None and p < 0.05 else "No",
        "student_t_statistic": format_number(st_stat),
        "student_degrees_of_freedom": format_number(st_df),
        "student_p_value": format_number(st_p, digits=6),
        "student_significant_0_05": "Yes" if st_p is not None and st_p < 0.05 else "No",
    }


# ── ORIGINAL GROUP A VS B ANALYSIS ───────────────────────────────────────────

def analyse_variable(rows, variable):
    group_a_values = [
        to_float(row.get(variable))
        for row in rows
        if row.get(GROUPING_VARIABLE) == GROUP_A
    ]
    group_b_values = [
        to_float(row.get(variable))
        for row in rows
        if row.get(GROUPING_VARIABLE) == GROUP_B
    ]
    group_a_values = [v for v in group_a_values if v is not None]
    group_b_values = [v for v in group_b_values if v is not None]

    result = run_t_tests(group_a_values, group_b_values)
    # Rename generic keys to original column names for backward compatibility
    return {
        "variable": variable,
        "group_a_n": result["group_1_n"],
        "group_a_mean": result["group_1_mean"],
        "group_a_sd": result["group_1_sd"],
        "group_b_n": result["group_2_n"],
        "group_b_mean": result["group_2_mean"],
        "group_b_sd": result["group_2_sd"],
        "mean_difference": result["mean_difference"],
        "t_statistic": result["t_statistic"],
        "degrees_of_freedom": result["degrees_of_freedom"],
        "p_value": result["p_value"],
        "significant_0_05": result["significant_0_05"],
        "student_t_statistic": result["student_t_statistic"],
        "student_degrees_of_freedom": result["student_degrees_of_freedom"],
        "student_p_value": result["student_p_value"],
        "student_significant_0_05": result["student_significant_0_05"],
    }


# ── NEW_GP PAIRWISE ANALYSIS ──────────────────────────────────────────────────

def analyse_new_gp_pairs(rows, outcome_variables):
    """
    Run all 15 pairwise t-tests between the 6 New_GP groups for each outcome variable.
    Returns a list of result rows.
    """
    output = []
    for variable in outcome_variables:
        # Build a dict: new_gp_label → list of numeric values
        group_values = {}
        for row in rows:
            gp_label = row.get("new_gp", "")
            if not gp_label:
                continue
            val = to_float(row.get(variable))
            if val is not None:
                group_values.setdefault(gp_label, []).append(val)

        for code_1, code_2 in NEW_GP_PAIRS:
            label_1 = NEW_GP_LABELS.get(code_1, str(code_1))
            label_2 = NEW_GP_LABELS.get(code_2, str(code_2))
            vals_1 = group_values.get(label_1, [])
            vals_2 = group_values.get(label_2, [])

            result = run_t_tests(vals_1, vals_2)
            output.append({
                "variable": variable,
                "comparison": f"{code_1} vs {code_2}",
                "group_1_code": code_1,
                "group_1_label": label_1,
                "group_2_code": code_2,
                "group_2_label": label_2,
                **result,
            })
    return output


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-file", default=DEFAULT_DATA_FILE)
    parser.add_argument("--form-label", default=DEFAULT_FORM_LABEL)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--new-gp-file", default=DEFAULT_NEW_GP_FILE)
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    # ── Standard Group A vs B t-tests ────────────────────────────────────────
    output_file = os.path.join(
        args.output_dir, f"{args.form_label}_groupwise_t_tests.csv"
    )
    rows = read_csv(args.data_file)
    school_reference = load_school_reference(SCHOOL_REFERENCE_FILE)

    for row in rows:
        add_group(row, school_reference)

    outcome_variables = resolve_outcome_variables(args.form_label)
    output_rows = [analyse_variable(rows, variable) for variable in outcome_variables]
    for row in output_rows:
        row["form_label"] = args.form_label
        row["source_file"] = args.data_file

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "form_label",
            "source_file",
            "variable",
            "group_a_n",
            "group_a_mean",
            "group_a_sd",
            "group_b_n",
            "group_b_mean",
            "group_b_sd",
            "mean_difference",
            "t_statistic",
            "degrees_of_freedom",
            "p_value",
            "significant_0_05",
            "student_t_statistic",
            "student_degrees_of_freedom",
            "student_p_value",
            "student_significant_0_05",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {output_file}")

    # ── New_GP pairwise t-tests ───────────────────────────────────────────────
    new_gp_reference = load_new_gp_reference(args.new_gp_file)
    if new_gp_reference:
        child_id_col = find_child_id_col(rows[0].keys()) if rows else None
        if child_id_col:
            apply_new_gp(rows, new_gp_reference, child_id_col)
            matched = sum(1 for r in rows if r.get("new_gp"))
            print(f"[t-tests] New_GP matched {matched}/{len(rows)} rows via '{child_id_col}'.")

            new_gp_rows = analyse_new_gp_pairs(rows, outcome_variables)
            for row in new_gp_rows:
                row["form_label"] = args.form_label
                row["source_file"] = args.data_file

            new_gp_output_file = os.path.join(
                args.output_dir, f"{args.form_label}_new_gp_t_tests.csv"
            )
            with open(new_gp_output_file, "w", newline="", encoding="utf-8") as file:
                fieldnames = [
                    "form_label",
                    "source_file",
                    "variable",
                    "comparison",
                    "group_1_code",
                    "group_1_label",
                    "group_2_code",
                    "group_2_label",
                    "group_1_n",
                    "group_1_mean",
                    "group_1_sd",
                    "group_2_n",
                    "group_2_mean",
                    "group_2_sd",
                    "mean_difference",
                    "t_statistic",
                    "degrees_of_freedom",
                    "p_value",
                    "significant_0_05",
                    "student_t_statistic",
                    "student_degrees_of_freedom",
                    "student_p_value",
                    "student_significant_0_05",
                ]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(new_gp_rows)
            print(f"Wrote {new_gp_output_file}")
        else:
            print("[t-tests] No child_id column found — New_GP pairwise t-tests skipped.")
    else:
        print("[t-tests] New_GP reference empty — New_GP pairwise t-tests skipped.")


if __name__ == "__main__":
    main()
