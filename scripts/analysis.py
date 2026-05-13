import subprocess
import sys

from form_registry import FORMS, data_file_for_form


DESCRIPTIVE_SCRIPT = "scripts/analysis_descriptives.py"
ADOLESCENT_ANALYSIS_SCRIPTS = [
    "scripts/analysis_descriptives.py",
    "scripts/analysis_reliability.py",
    "scripts/analysis_groupwise_t_tests.py",
]


def main():
    for form_config in FORMS:
        data_file = data_file_for_form(form_config)
        form_label = form_config["label"]
        scripts = [DESCRIPTIVE_SCRIPT]
        if form_config.get("respondent") == "adolescent":
            scripts = ADOLESCENT_ANALYSIS_SCRIPTS

        for script in scripts:
            subprocess.run(
                [
                    sys.executable,
                    script,
                    "--data-file",
                    data_file,
                    "--form-label",
                    form_label,
                ],
                check=True,
            )


if __name__ == "__main__":
    main()
