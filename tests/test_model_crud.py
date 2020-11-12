# _*_ coding: utf-8 _*_
import uuid
from datetime import datetime

import pytest
from fhir.resources.patient import Patient
from fhirpath.enums import FHIR_VERSION
from fhirpath.json import json_loads

from hyperfhir.api import tasks
from hyperfhir.models import crud
from hyperfhir.models.resource import ResourceHistoryModel
from tests._utils import FHIR_EXAMPLE_RESOURCES


@pytest.mark.asyncio
async def test_create_resource(pg_connection):
    """ """
    db = pg_connection
    resource_obj = Patient.parse_file(FHIR_EXAMPLE_RESOURCES / "Patient.json")
    resource_obj.id = str(uuid.uuid4())
    resource_obj.meta = {"versionId": "1", "lastUpdated": datetime.utcnow()}
    res1 = await crud.create_resource(db, resource_obj, FHIR_VERSION.R4)
    await tasks.add_resource_history(db, res1, first=True)
    await tasks.add_resource_history(db, res1, first=False)

    result = await db.fetch_all(
        f"SELECT * FROM {ResourceHistoryModel.__tablename__} ORDER BY id ASC"
    )
    assert len(result) == 2
    assert result[0]["next_id"] == result[1]["id"]
    assert result[0]["id"] == result[1]["prev_id"]
