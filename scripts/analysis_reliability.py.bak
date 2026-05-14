import csv
import os
import argparse
from statistics import variance

OUTPUT_DIR = "output"
DEFAULT_DATA_FILE = "data/SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Adolescents)_v1_0.csv"
DEFAULT_FORM_LABEL = "6_month_follow_up_adolescents"


MEASURES = [
    {
        "outcome_measure": "PHQ9",
        "total_score_variable": "phq9a_-phq9a_total",
        "items": [f"phq9a_-phq9a_item_{i:02d}" for i in range(1, 10)],
    },
    {
        "outcome_measure": "PSC",
        "total_score_variable": "psc_-psc_total",
        "items": [
            *[f"psc_-psc_item_{i:02d}" for i in range(1, 29)],
            "psc_-psc_item_29r",
            "psc_-psc_item_30r",
            "psc_-psc_item_31r",
            "psc_-psc_item_32",
            "psc_-psc_item_33",
            "psc_-psc_item_34",
            "psc_-psc_item_35r",
        ],
    },
    {
        "outcome_measure": "RCADS",
        "total_score_variable": "rcads_-rcads_total",
        "items": [f"rcads_-rcads_item_{i:02d}" for i in range(1, 26)],
    },
    {
        "outcome_measure": "DSM-5",
        "total_score_variable": "dsm5_-dsm5_total",
        "items": [f"dsm5_-dsm_item_{i:02d}" for i in range(1, 23)],
    },
    {
        "outcome_measure": "Somatic",
        "total_score_variable": "somatic_-somatic_total",
        "items": [f"somatic_-somatic_item_04{suffix}" for suffix in "abcdefgh"],
    },
    {
        "outcome_measure": "WEMWBS",
        "total_score_variable": "wemwbs_-wemwbs_total",
        "items": [f"wemwbs_-wemwbs_item_{i:02d}" for i in range(1, 8)],
    },
    {
        "outcome_measure": "SPSI",
        "total_score_variable": "spsi_-spsi_total",
        "items": [f"spsi_-spsi_item_{i:02d}" for i in range(1, 26)],
    },
    {
        "outcome_measure": "IBS",
        "total_score_variable": "ibs_-ibs_total",
        "items": [f"ibs_-ibs_item_{i:02d}" for i in range(1, 5)],
    },
    {
        "outcome_measure": "BBSCQ",
        "total_score_variable": "bbscq_-bbscq_total",
        "items": [f"bbscq_-bbscq_item_{i:02d}" for i in range(1, 29)],
    },
    {
        "outcome_measure": "Self Stigma",
        "total_score_variable": "self_stigma_-stgt_total",
        "items": [f"self_stigma_-stgt_item_{i:02d}" for i in range(1, 6)],
    },
    {
        "outcome_measure": "Psychlops-Post",
        "total_score_variable": "psychlops_post_-psy_total",
        "items": [
            "psychlops_post_-psy_Q1b",
            "psychlops_post_-psy_Q2b",
            "psychlops_post_-psy_Q3b",
            "psychlops_post_-psy_Q4",
        ],
    },
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
        return float(value)
    except ValueError:
        return None


def cronbach_alpha(complete_rows, items):
    k = len(items)
    if k < 2 or len(complete_rows) < 2:
        return None

    item_variances = []
    for item in items:
        item_values = [row[item] for row in complete_rows]
        item_variances.append(variance(item_values))

    total_scores = [sum(row[item] for item in items) for row in complete_rows]
    total_variance = variance(total_scores)
    if total_variance == 0:
        return None

    return (k / (k - 1)) * (1 - (sum(item_variances) / total_variance))


def analyse_measure(rows, measure, available_columns):
    items = measure["items"]
    missing_items = [item for item in items if item not in available_columns]
    available_items = [item for item in items if item in available_columns]

    complete_rows = []
    for row in rows:
        values = {item: to_float(row.get(item)) for item in available_items}
        if len(values) == len(items) and all(value is not None for value in values.values()):
            complete_rows.append(values)

    alpha = cronbach_alpha(complete_rows, available_items) if not missing_items else None
    return {
        "outcome_measure": measure["outcome_measure"],
        "total_score_variable": measure["total_score_variable"],
        "number_of_items": len(items),
        "n_complete_cases": len(complete_rows),
        "cronbach_alpha": f"{alpha:.4f}" if alpha is not None else "",
        "missing_items": "; ".join(missing_items),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-file", default=DEFAULT_DATA_FILE)
    parser.add_argument("--form-label", default=DEFAULT_FORM_LABEL)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    output_file = os.path.join(args.output_dir, f"{args.form_label}_reliability_cronbach_alpha.csv")
    rows = read_csv(args.data_file)
    available_columns = set(rows[0].keys()) if rows else set()

    output_rows = [
        analyse_measure(rows, measure, available_columns)
        for measure in MEASURES
    ]
    for row in output_rows:
        row["form_label"] = args.form_label
        row["source_file"] = args.data_file

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "form_label",
            "source_file",
            "outcome_measure",
            "total_score_variable",
            "number_of_items",
            "n_complete_cases",
            "cronbach_alpha",
            "missing_items",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {output_file}")


if __name__ == "__main__":
    main()
