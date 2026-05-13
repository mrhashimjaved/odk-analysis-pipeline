import requests
import os
from urllib.parse import quote

from form_registry import FORMS
from local_env import load_repo_env

load_repo_env()

ODK_URL = os.environ["ODK_URL"].rstrip("/")
EMAIL = os.environ["ODK_EMAIL"]
PASSWORD = os.environ["ODK_PASSWORD"]

session = requests.Session()

# Login
login = session.post(
    f"{ODK_URL}/v1/sessions",
    json={"email": EMAIL, "password": PASSWORD},
    timeout=60
)
login.raise_for_status()

os.makedirs("data", exist_ok=True)


def print_available_forms(project_id):
    forms_url = f"{ODK_URL}/v1/projects/{project_id}/forms"
    forms = session.get(forms_url, timeout=60)
    forms.raise_for_status()

    print(f"Available forms in project {project_id}:")
    for form in forms.json():
        xml_form_id = form.get("xmlFormId", "")
        name = form.get("name", "")
        print(f"- {xml_form_id} ({name})")


# Fetch each form
for f in FORMS:
    form_id = quote(f["form"], safe="")
    url = f"{ODK_URL}/v1/projects/{f['project']}/forms/{form_id}/submissions.csv"
    r = session.get(url, timeout=120)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        if r.status_code == 404:
            print_available_forms(f["project"])
        raise

    filename = f"data/{f['form']}.csv"
    with open(filename, "wb") as file:
        file.write(r.content)

    print(f"Downloaded {filename}")
