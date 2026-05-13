import csv
import math
import os
from statistics import mean, stdev, variance


DATA_FILE = "data/SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Adolescents)_v1_0.csv"
SCHOOL_REFERENCE_FILE = "data/school_group_reference.csv"
OUTPUT_DIR = "output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "groupwise_t_tests.csv")

GROUPING_VARIABLE = "group"
GROUP_A = "A"
GROUP_B = "B"

OUTCOME_VARIABLES = [
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
    school_id = (row.get("demo_a_-sch_id") or row.get("demo_b_-csv_sch_id") or "").strip()
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
    denominator = ((var_a / n_a) ** 2 / (n_a - 1)) + ((var_b / n_b) ** 2 / (n_b - 1))
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
    pooled_variance = (((n_a - 1) * var_a) + ((n_b - 1) * var_b)) / degrees_of_freedom
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
    group_a_values = [value for value in group_a_values if value is not None]
    group_b_values = [value for value in group_b_values if value is not None]

    t_statistic, degrees_of_freedom, p_value = welch_t_test(group_a_values, group_b_values)
    student_t_statistic, student_degrees_of_freedom, student_p_value = student_t_test(
        group_a_values,
        group_b_values,
    )
    mean_a = mean(group_a_values) if group_a_values else None
    mean_b = mean(group_b_values) if group_b_values else None

    return {
        "variable": variable,
        "group_a_n": len(group_a_values),
        "group_a_mean": format_number(mean_a),
        "group_a_sd": format_number(stdev(group_a_values) if len(group_a_values) > 1 else None),
        "group_b_n": len(group_b_values),
        "group_b_mean": format_number(mean_b),
        "group_b_sd": format_number(stdev(group_b_values) if len(group_b_values) > 1 else None),
        "mean_difference": format_number(mean_a - mean_b if mean_a is not None and mean_b is not None else None),
        "t_statistic": format_number(t_statistic),
        "degrees_of_freedom": format_number(degrees_of_freedom),
        "p_value": format_number(p_value, digits=6),
        "significant_0_05": "Yes" if p_value is not None and p_value < 0.05 else "No",
        "student_t_statistic": format_number(student_t_statistic),
        "student_degrees_of_freedom": format_number(student_degrees_of_freedom),
        "student_p_value": format_number(student_p_value, digits=6),
        "student_significant_0_05": "Yes" if student_p_value is not None and student_p_value < 0.05 else "No",
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rows = read_csv(DATA_FILE)
    school_reference = load_school_reference(SCHOOL_REFERENCE_FILE)

    for row in rows:
        add_group(row, school_reference)

    output_rows = [analyse_variable(rows, variable) for variable in OUTCOME_VARIABLES]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        fieldnames = [
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

    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
