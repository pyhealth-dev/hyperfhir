import pytest
from fhirpath.utils import json_loads
from fhir.resources.bundle import Bundle
from hyperfhir.db import get_db
from hyperfhir.models.resource import ResourceHistoryModel
from tests._utils import FHIR_EXAMPLE_RESOURCES


@pytest.mark.asyncio
async def test_resource_search(hyperfhir_site, es_data):
    """ """
    client = hyperfhir_site
    res = await client.get(
        "/api/v1/fhir/Patient",
        headers={"Accept": "application/json"},
    )
    bundle = Bundle.parse_raw(res.content)
    assert bundle.total == 1

    res = await client.get(
        "/api/v1/fhir/Patient?identifier=CPR|240365-0002",
        headers={"Accept": "application/json"},
    )
    bundle = Bundle.parse_raw(res.content)
    assert bundle.total == 1
