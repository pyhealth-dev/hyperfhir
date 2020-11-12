import typing
from datetime import datetime

from databases import Database
from fhirpath.enums import FHIR_VERSION

from .resource import ResourceHistoryModel, ResourceTransactionModel

if typing.TYPE_CHECKING:
    from fhir.resources.domainresource import DomainResource

__author__ = "Md Nazrul Islam<>"


async def create_resource(
    db: Database, resource: "DomainResource", fhir_version: FHIR_VERSION
):
    """
    https://github.com/MagicStack/asyncpg/issues/526
    :param db:
    :param resource:
    :param fhir_version:
    :return:
    """
    es_id = "{0}_{1}_{2}".format(
        fhir_version.name.lower(),
        resource.resource_type.lower(),
        resource.id.replace("-", ""),
    )
    resource_id = resource.id
    status = "created"
    resource_type = resource.resource_type
    resource_version = resource.meta.versionId
    resource = resource.json()
    fhir_version = fhir_version.value
    timestamp = datetime.utcnow()

    query1 = (
        f"INSERT INTO {ResourceTransactionModel.__tablename__}(es_id, resource_id, status, resource_type, "
        "resource_version, resource, fhir_version, timestamp) VALUES (:es_id, :resource_id, "
        ":status, :resource_type, :resource_version, :resource, :fhir_version, :timestamp) RETURNING id"
    )
    data1 = {
        "es_id": es_id,
        "resource_id": resource_id,
        "status": status,
        "resource_type": resource_type,
        "resource_version": resource_version,
        "resource": resource,
        "fhir_version": fhir_version,
        "timestamp": timestamp,
    }
    async with db.transaction():
        primary_key = await db.execute(query1, values=data1)
        data1["id"] = primary_key

    return data1
