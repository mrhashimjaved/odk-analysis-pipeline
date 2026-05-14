import subprocess
import sys
from pathlib import Path

from form_registry import FORMS, data_file_for_form

NEW_GP_FILE = "data/New_GP.xlsx"

ANALYSIS_SCRIPTS = [
    "scripts/analysis_descriptives.py",
    "scripts/analysis_reliability.py",
    "scripts/analysis_groupwise_t_tests.py",
]

REPORT_SCRIPT = "scripts/generate_report.py"
REPORT_DOCX_SCRIPT = "scripts/generate_report_docx.py"


def report_python_executable():
    bundled = Path(
        r"C:\Users\mhj__\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    )
    if bundled.exists():
        return str(bundled)
    return sys.executable


def main():
    for form_config in FORMS:
        data_file = data_file_for_form(form_config)
        form_label = form_config["label"]

        for script in ANALYSIS_SCRIPTS:
            subprocess.run(
                [
                    sys.executable,
                    script,
                    "--data-file", data_file,
                    "--form-label", form_label,
                    "--new-gp-file", NEW_GP_FILE,
                ],
                check=True,
            )

    report_python = report_python_executable()
    subprocess.run([report_python, REPORT_SCRIPT], check=True)
    subprocess.run([report_python, REPORT_DOCX_SCRIPT], check=True)


if __name__ == "__main__":
    main()
