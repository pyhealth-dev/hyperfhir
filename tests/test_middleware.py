"""Middleware """
import pytest


@pytest.mark.asyncio
async def test_http_fhir_request(hyperfhir_site):
    """ """
    client = hyperfhir_site
    res = await client.get(
        "/api/v1/fhir/Organization/_history?_pretty=true",
        headers={
            "Accept": "application/fhir+json; fhirVersion=4.0",
            "If-None-Exist": "identifier=http://my-lab-system|123",
            "If-None-Match": 'W/"456"',
        },
    )
