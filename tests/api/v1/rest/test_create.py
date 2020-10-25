from tests._utils import FHIR_EXAMPLE_RESOURCES
from fhirpath.utils import json_loads

def test_create_patient(hyperfhir_site):
    """ """
    client, app = hyperfhir_site
    with open(str(FHIR_EXAMPLE_RESOURCES / "Patient.json"), "rb") as fp:
        json_data = json_loads(fp.read())

    res = client.post("/api/v1/fhir/Patient", json=json_data, headers={"Accept": "application/json"})
    breakpoint()
