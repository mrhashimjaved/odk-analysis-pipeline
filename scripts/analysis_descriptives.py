import csv
import math
import os
from collections import Counter, defaultdict
from statistics import mean, stdev


DATA_FILE = "data/SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Adolescents)_v1_0.csv"
SCHOOL_REFERENCE_FILE = "data/school_group_reference.csv"
OUTPUT_DIR = "output"

CONTINUOUS_OUTPUT = os.path.join(OUTPUT_DIR, "descriptives_continuous.csv")
CATEGORICAL_OUTPUT = os.path.join(OUTPUT_DIR, "descriptives_categorical.csv")
MISSING_OUTPUT = os.path.join(OUTPUT_DIR, "descriptives_missing_variables.csv")
SUMMARY_OUTPUT = os.path.join(OUTPUT_DIR, "descriptives_summary.txt")


OVERALL_VARIABLES = [
    "phq9a_-phq9a_total",
    "psc_-psc_total",
    "rcads_-rcads_total",
    "dsm5_-dsm5_total",
    "somatic_-somatic_total",
    "wemwbs_-wemwbs_total",
    "ibs_-ibs_total",
    "bbscq_-bbscq_total",
    "cgas_-cgas_response",
    "self_stigma_-stgt_total",
    "psychlops_post_-psy_total",
]

DOMAIN_VARIABLES = {
    "PHQ9": [
        "phq9a_-phq9a_total",
        "phq9a_-phq9a_total_cat_bin",
        "phq9a_-phq9a_total_cat",
    ],
    "PSC": [
        "psc_-psc_total",
        "psc_-psc_int",
        "psc_-psc_ext",
        "psc_-psc_attn",
        "psc_-psc_total_cat",
    ],
    "RCADS": [
        "rcads_-rcads_total",
        "rcads_-rcads_anx_tot",
        "rcads_-rcads_dep_tot",
    ],
    "DSM-5": [
        "dsm5_-dsm5_total",
        "dsm5_-dsm5_I_Som_Symp",
        "dsm5_-dsm5_II_Slp_prb",
        "dsm5_-dsm5_III_Inattn",
        "dsm5_-dsm5_IV_Dep",
        "dsm5_-dsm5_V_VI_Angr_Irrit",
        "dsm5_-dsm5_VII_Mania",
        "dsm5_-dsm5_VIII_Anx",
        "dsm5_-dsm5_IX_Psychss",
        "dsm5_-dsm5_X_Rpt_thts",
        "dsm5_-dsm5_XI_Sbtncd",
        "dsm5_-dsm5_XII_Suic",
    ],
    "SOMATIC": [
        "somatic_-somatic_total",
        "somatic_-somatic_item_01",
        "somatic_-somatic_item_02",
        "somatic_-somatic_item_03",
        "somatic_-somatic_item_04a",
        "somatic_-somatic_item_04b",
        "somatic_-somatic_item_04c",
        "somatic_-somatic_item_04d",
        "somatic_-somatic_item_04e",
        "somatic_-somatic_item_04f",
        "somatic_-somatic_item_04g",
        "somatic_-somatic_item_04h",
    ],
    "WEMWBS": [
        "wemwbs_-wemwbs_total",
        "wemwbs_-wemwbs_item_01",
        "wemwbs_-wemwbs_item_02",
        "wemwbs_-wemwbs_item_03",
        "wemwbs_-wemwbs_item_04",
        "wemwbs_-wemwbs_item_05",
        "wemwbs_-wemwbs_item_06",
        "wemwbs_-wemwbs_item_07",
    ],
    "SPSI": [
        "spsi_-spsi_ppo",
        "spsi_-spsi_npo",
        "spsi_-spsi_rps",
        "spsi_-spsi_ics",
        "spsi_-spsi_as",
    ],
    "BBSCQ": [
        "bbscq_-bbscq_total",
        "bbscq_-bbscq_relation",
        "bbscq_-bbscq_belonging",
        "bbscq_-bbscq_comitment",
        "bbscq_-bbscq_participation",
    ],
}

GROUPING_VARIABLES = ["group", "gender", "new_group"]


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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


def school_gender(school_id):
    school_id = (school_id or "").strip().upper()
    if school_id.startswith("B"):
        return "Boys"
    if school_id.startswith("G"):
        return "Girls"
    return ""


def load_school_reference(path):
    reference = {}
    for row in read_csv(path):
        school_id = row["school_id"].strip()
        reference[school_id] = {
            "school_name": row["school_name"].strip(),
            "group": row["group"].strip(),
        }
    return reference


def add_generated_variables(row):
    phq9_total = to_float(row.get("phq9a_-phq9a_total"))
    if phq9_total is None:
        row["phq9a_-phq9a_total_cat_bin"] = ""
        row["phq9a_-phq9a_total_cat"] = ""
        return

    row["phq9a_-phq9a_total_cat_bin"] = "0" if phq9_total < 5 else "1"

    if phq9_total < 5:
        row["phq9a_-phq9a_total_cat"] = "1"
    elif phq9_total <= 9:
        row["phq9a_-phq9a_total_cat"] = "2"
    elif phq9_total <= 14:
        row["phq9a_-phq9a_total_cat"] = "3"
    elif phq9_total <= 19:
        row["phq9a_-phq9a_total_cat"] = "4"
    elif phq9_total <= 27:
        row["phq9a_-phq9a_total_cat"] = "5"
    else:
        row["phq9a_-phq9a_total_cat"] = ""


def add_grouping_variables(row, school_reference):
    school_id = (row.get("demo_a_-sch_id") or row.get("demo_b_-csv_sch_id") or "").strip()
    school = school_reference.get(school_id, {})
    group = school.get("group", "")
    gender = school_gender(school_id)

    row["school_id"] = school_id
    row["school_name"] = school.get("school_name", "")
    row["group"] = group
    row["gender"] = gender
    row["new_group"] = f"{group}_{gender}" if group and gender else ""


def variable_catalog():
    catalog = []
    for variable in OVERALL_VARIABLES:
        catalog.append({"analysis_set": "Overall", "domain": "Overall", "variable": variable})
    for domain, variables in DOMAIN_VARIABLES.items():
        for variable in variables:
            catalog.append({"analysis_set": "Domain wise", "domain": domain, "variable": variable})
    return catalog


def format_number(value):
    if value == "":
        return ""
    return f"{value:.2f}"


def is_categorical_variable(variable):
    return (
        variable == "cgas_-cgas_response"
        or variable.endswith("_cat")
        or variable.endswith("_cat_bin")
    )


def variable_type(variable):
    return "categorical" if is_categorical_variable(variable) else "continuous"


def continuous_stats(rows, catalog):
    output = []
    for item in catalog:
        variable = item["variable"]
        if is_categorical_variable(variable):
            continue
        output.extend(continuous_rows_for_group(rows, item, "overall", "overall"))
        for grouping_variable in GROUPING_VARIABLES:
            values = sorted({row.get(grouping_variable, "") for row in rows if row.get(grouping_variable, "")})
            for group_value in values:
                group_rows = [row for row in rows if row.get(grouping_variable) == group_value]
                output.extend(continuous_rows_for_group(group_rows, item, grouping_variable, group_value))
    return output


def continuous_rows_for_group(rows, item, grouping_variable, group_value):
    variable = item["variable"]
    values = [to_float(row.get(variable)) for row in rows]
    values = [value for value in values if value is not None]
    n = len(values)
    if n == 0:
        return [{
            **item,
            "variable_type": variable_type(variable),
            "group_by": grouping_variable,
            "group_value": group_value,
            "n": 0,
            "mean": "",
            "sd": "",
            "min": "",
            "max": "",
            "min_max": "",
        }]

    min_value = min(values)
    max_value = max(values)
    return [{
        **item,
        "variable_type": variable_type(variable),
        "group_by": grouping_variable,
        "group_value": group_value,
        "n": n,
        "mean": format_number(mean(values)),
        "sd": format_number(stdev(values)) if n > 1 else "",
        "min": format_number(min_value),
        "max": format_number(max_value),
        "min_max": f"{format_number(min_value)}-{format_number(max_value)}",
    }]


def categorical_stats(rows, catalog):
    output = []
    for item in catalog:
        variable = item["variable"]
        if not is_categorical_variable(variable):
            continue
        output.extend(categorical_rows_for_group(rows, item, "overall", "overall"))
        for grouping_variable in GROUPING_VARIABLES:
            values = sorted({row.get(grouping_variable, "") for row in rows if row.get(grouping_variable, "")})
            for group_value in values:
                group_rows = [row for row in rows if row.get(grouping_variable) == group_value]
                output.extend(categorical_rows_for_group(group_rows, item, grouping_variable, group_value))
    return output


def categorical_rows_for_group(rows, item, grouping_variable, group_value):
    variable = item["variable"]
    values = [str(row.get(variable, "")).strip() for row in rows]
    values = [value for value in values if value != ""]
    n = len(values)
    counts = Counter(values)
    output = []
    for category in sorted(counts, key=category_sort_key):
        freq = counts[category]
        output.append({
            **item,
            "variable_type": variable_type(variable),
            "group_by": grouping_variable,
            "group_value": group_value,
            "category": category,
            "n": n,
            "freq": freq,
            "percentage": format_number((freq / n) * 100) if n else "",
        })
    if not output:
        output.append({
            **item,
            "variable_type": variable_type(variable),
            "group_by": grouping_variable,
            "group_value": group_value,
            "category": "",
            "n": 0,
            "freq": 0,
            "percentage": "",
        })
    return output


def category_sort_key(value):
    number = to_float(value)
    if number is None:
        return (1, value)
    return (0, number)


def missing_variables(rows, catalog):
    available = set(rows[0].keys()) if rows else set()
    return [
        item
        for item in catalog
        if item["variable"] not in available
    ]


def write_summary(rows, catalog, continuous_rows, categorical_rows, missing_rows):
    group_counts = defaultdict(Counter)
    for row in rows:
        for grouping_variable in GROUPING_VARIABLES:
            value = row.get(grouping_variable, "")
            if value:
                group_counts[grouping_variable][value] += 1

    with open(SUMMARY_OUTPUT, "w", encoding="utf-8") as file:
        file.write("Adolescent descriptives summary\n")
        file.write("===============================\n\n")
        file.write(f"Input data: {DATA_FILE}\n")
        file.write(f"School reference: {SCHOOL_REFERENCE_FILE}\n")
        file.write(f"Rows analysed: {len(rows)}\n\n")

        file.write("Group counts\n")
        file.write("------------\n")
        for grouping_variable in GROUPING_VARIABLES:
            file.write(f"{grouping_variable}:\n")
            for value, count in sorted(group_counts[grouping_variable].items()):
                file.write(f"  {value}: {count}\n")
            file.write("\n")

        file.write("Outputs\n")
        file.write("-------\n")
        file.write("Descriptive statistics:\n")
        file.write("  Continuous variables: N, Mean, SD, Min-Max\n")
        file.write("  Categorical variables ending in '_cat' or '_cat_bin': N, Freq, Percentage\n")
        file.write("  Additional categorical variable: cgas_-cgas_response\n")
        file.write(f"Continuous descriptives: {CONTINUOUS_OUTPUT} ({len(continuous_rows)} rows)\n")
        file.write(f"Categorical descriptives: {CATEGORICAL_OUTPUT} ({len(categorical_rows)} rows)\n")
        file.write(f"Missing variable report: {MISSING_OUTPUT} ({len(missing_rows)} rows)\n\n")

        file.write("Descriptive Statistics of Outcome variables (Overall)\n")
        file.write("-----------------------------------------------------\n")
        write_summary_section(file, catalog, "Overall", continuous_rows, categorical_rows)
        file.write("\n")

        file.write("Descriptive Statistics of Outcome variables (Domain wise)\n")
        file.write("---------------------------------------------------------\n")
        write_summary_section(file, catalog, "Domain wise", continuous_rows, categorical_rows)
        file.write("\n")

        if missing_rows:
            file.write("Missing variables\n")
            file.write("-----------------\n")
            for row in missing_rows:
                file.write(f"{row['analysis_set']} | {row['domain']} | {row['variable']}\n")
        else:
            file.write("No requested analysis variables were missing.\n")


def write_summary_section(file, catalog, analysis_set, continuous_rows, categorical_rows):
    items = [item for item in catalog if item["analysis_set"] == analysis_set]
    continuous_variables = [item["variable"] for item in items if not is_categorical_variable(item["variable"])]
    categorical_variables = [item["variable"] for item in items if is_categorical_variable(item["variable"])]
    continuous_output_rows = [row for row in continuous_rows if row["analysis_set"] == analysis_set]
    categorical_output_rows = [row for row in categorical_rows if row["analysis_set"] == analysis_set]

    file.write(f"Continuous variables: {len(continuous_variables)}\n")
    for variable in continuous_variables:
        file.write(f"  - {variable}\n")
    file.write(f"Categorical variables: {len(categorical_variables)}\n")
    for variable in categorical_variables:
        file.write(f"  - {variable}\n")
    file.write(f"Output rows: {len(continuous_output_rows)} continuous, {len(categorical_output_rows)} categorical\n")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rows = read_csv(DATA_FILE)
    school_reference = load_school_reference(SCHOOL_REFERENCE_FILE)

    for row in rows:
        add_grouping_variables(row, school_reference)
        add_generated_variables(row)

    catalog = variable_catalog()
    missing_rows = missing_variables(rows, catalog)
    continuous_rows = continuous_stats(rows, catalog)
    categorical_rows = categorical_stats(rows, catalog)

    write_csv(CONTINUOUS_OUTPUT, continuous_rows, [
        "analysis_set",
        "domain",
        "variable",
        "variable_type",
        "group_by",
        "group_value",
        "n",
        "mean",
        "sd",
        "min",
        "max",
        "min_max",
    ])
    write_csv(CATEGORICAL_OUTPUT, categorical_rows, [
        "analysis_set",
        "domain",
        "variable",
        "variable_type",
        "group_by",
        "group_value",
        "category",
        "n",
        "freq",
        "percentage",
    ])
    write_csv(MISSING_OUTPUT, missing_rows, [
        "analysis_set",
        "domain",
        "variable",
    ])
    write_summary(rows, catalog, continuous_rows, categorical_rows, missing_rows)

    print(f"Wrote {CONTINUOUS_OUTPUT}")
    print(f"Wrote {CATEGORICAL_OUTPUT}")
    print(f"Wrote {MISSING_OUTPUT}")
    print(f"Wrote {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
