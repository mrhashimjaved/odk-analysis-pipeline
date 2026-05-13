FORMS = [
    {
        "project": 5,
        "form": "SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Adolescents)_v1_0",
        "label": "6_month_follow_up_adolescents",
        "respondent": "adolescent",
    },
    {
        "project": 5,
        "form": "SMART_STEP_6_Month_Follow_Up_Assessment_Pack_(Caregiver)_v1_0",
        "label": "6_month_follow_up_caregiver",
        "respondent": "caregiver",
    },
    {
        "project": 5,
        "form": "SMART_STEP_9_Month_Endpoint_Assessment_Pack_(Adolescents)_v1_0",
        "label": "9_month_endpoint_adolescents",
        "respondent": "adolescent",
    },
    {
        "project": 5,
        "form": "SMART_STEP_9_Month_Endpoint_Assessment_Pack_(Caregiver)_v1_0",
        "label": "9_month_endpoint_caregiver",
        "respondent": "caregiver",
    },
]


def data_file_for_form(form_config):
    return f"data/{form_config['form']}.csv"
