import requests
import os

ODK_URL = os.environ["ODK_URL"]
EMAIL = os.environ["ODK_EMAIL"]
PASSWORD = os.environ["ODK_PASSWORD"]

# Multiple forms
FORMS = [
    {
        "project": 5,
        "form": "SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Caregiver)_v1_0"
    },
    # add more here
]

session = requests.Session()

# Login
session.post(
    f"{ODK_URL}/v1/sessions",
    json={"email": EMAIL, "password": PASSWORD}
)

# Fetch each form
for f in FORMS:
    url = f"{ODK_URL}/v1/projects/{f['project']}/forms/{f['form']}.svc/Submissions.csv"
    r = session.get(url)

    filename = f"data/{f['form']}.csv"
    with open(filename, "wb") as file:
        file.write(r.content)

    print(f"Downloaded {filename}")