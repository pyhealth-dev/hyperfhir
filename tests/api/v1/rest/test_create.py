import pytest
from fhirpath.utils import json_loads

from hyperfhir.db import get_db
from hyperfhir.models.resource import ResourceHistoryModel
from tests._utils import FHIR_EXAMPLE_RESOURCES


@pytest.mark.asyncio
async def test_create_patient(hyperfhir_site, es_setup):
    """ """
    client = hyperfhir_site
    with open(str(FHIR_EXAMPLE_RESOURCES / "Patient.json"), "rb") as fp:
        json_data = json_loads(fp.read())

    res = await client.post(
        "/api/v1/fhir/Patient",
        json=json_data,
        headers={"Accept": "application/json"},
    )
    assert res.status_code == 201
    db = get_db()
    result = await db.fetch_all(
        f"SELECT * FROM {ResourceHistoryModel.__tablename__} ORDER BY id ASC"
    )
    assert len(result) == 1
