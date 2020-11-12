import typing

from databases import Database
from fhirpath.json import json_loads

from hyperfhir.db.es import ElasticsearchEngine
from hyperfhir.models.resource import ResourceHistoryModel

__author__ = "Md Nazrul Islam<email2nazrul@gmail.com>"


async def add_resource_history(
    db: Database, record: typing.Dict[str, typing.Any], first: bool = True
):
    """ """
    data = record.copy()
    data["txid"] = data.pop("id")
    data["prev_id"] = None
    del data["es_id"]

    if first is False:
        previous_pk = await db.fetch_val(
            (
                f"SELECT id FROM {ResourceHistoryModel.__tablename__} "
                "WHERE txid=:txid ORDER BY timestamp DESC LIMIT 1"
            ),
            values={"txid": data["txid"]},
            column="id",
        )
        if previous_pk:
            data["prev_id"] = previous_pk

    async with db.transaction():
        query1 = (
            f"INSERT INTO {ResourceHistoryModel.__tablename__}"
            "(txid, resource_id, prev_id, status, resource_type, "
            "resource_version, resource, fhir_version, timestamp) "
            "VALUES (:txid, :resource_id, :prev_id, :status, :resource_type, "
            ":resource_version, :resource, :fhir_version, :timestamp) RETURNING id"
        )
        pk = await db.execute(query1, values=data)
        if data["prev_id"]:
            query2 = (
                f"UPDATE {ResourceHistoryModel.__tablename__} "
                "SET next_id=:next_id "
                "WHERE id=:id"
            )
            await db.execute(query2, values={"next_id": pk, "id": data["prev_id"]})


async def add_elasticsearch_doc(
    es_engine: ElasticsearchEngine,
    record: typing.Dict[str, typing.Any],
    create: bool = True,
):
    """ """
    index_name = es_engine.get_index_name()
    doc_type = es_engine.get_doc_type()
    conn = es_engine.connection.raw_connection

    if create is False:
        await conn.delete(index_name, record["es_id"], doc_type=doc_type)
    body = {
        es_engine.calculate_field_index_name(
            resource_type=record["resource_type"]
        ): json_loads(record["resource"])
    }
    await conn.create(
        index_name, record["es_id"], body, doc_type=doc_type, refresh=True
    )
