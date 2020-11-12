# _*_ coding: utf-8 _*_
import datetime
import os
import pathlib
import subprocess
import time
import uuid

import elasticsearch
import pytz
from fhirpath.json import json_loads

from hyperfhir.db.es import _get_doc_type, _get_index_name

__author__ = "Md Nazrul Islam<email2nazrul@gmail.com>"

FHIR_EXAMPLE_RESOURCES = (
    pathlib.Path(os.path.abspath(__file__)).parent / "_static" / "FHIR"
)
IS_TRAVIS = os.environ.get("TRAVIS", "") != ""


def has_internet_connection():
    """ """
    try:
        res = subprocess.check_call(["ping", "-c", "1", "8.8.8.8"])
        return res == 0
    except subprocess.CalledProcessError:
        return False


async def load_organizations_data(es_conn, *, index_name, count=1):
    """ """
    added = 0
    conn = es_conn.raw_connection

    while count > added:
        organization_data = _make_index_item("Organization")
        bulk_data = [
            {"index": {"_id": organization_data["uuid"], "_index": index_name}},
            organization_data,
        ]
        res = await conn.bulk(
            index=index_name, doc_type=_get_doc_type(), body=bulk_data
        )
        assert res["errors"] is False
        added += 1
        if added % 100 == 0:
            time.sleep(1)

    conn.indices.refresh(index=index_name)


def _make_index_item(resource_type):
    """ """
    now_time = datetime.datetime.now()
    now_time.replace(tzinfo=pytz.UTC)

    tpl = {
        "access_roles": [
            "hfa.Reader",
            "hfa.Reviewer",
            "hfa.Owner",
            "hfa.Editor",
            "hfa.ContainerAdmin",
        ],
        "access_users": ["root"],
    }

    with open(str(FHIR_EXAMPLE_RESOURCES / (resource_type + ".json")), "rb") as fp:
        data = json_loads(fp.read())

    tpl[resource_type] = data
    tpl["uid"] = uuid.uuid4().hex
    return tpl


def _load_es_data(es_conn, release_name="R4"):
    """ """

    def _make_es_id(data, release_name_, resource_name):
        """
        :param data:
        :param release_name_:
        :param resource_name:
        :return:
        """
        return "_".join(
            [
                release_name_.lower(),
                resource_name.lower(),
                data["uid"].pop(),
            ]
        )

    conn = es_conn.raw_connection
    index_name = _get_index_name(release_name)
    organization_data = _make_index_item("Organization")
    bulk_data = [
        {
            "index": {
                "_id": _make_es_id(organization_data, release_name, "Organization"),
                "_index": _get_index_name(release_name),
            }
        },
        organization_data,
    ]
    res = conn.bulk(
        index=_get_index_name(release_name), doc_type=_get_doc_type(), body=bulk_data
    )
    assert res["errors"] is False

    patient_data = _make_index_item("Patient")
    bulk_data = [
        {
            "index": {
                "_id": _make_es_id(patient_data, release_name, "Patient"),
                "_index": index_name,
            }
        },
        patient_data,
    ]
    res = conn.bulk(index=index_name, doc_type=_get_doc_type(), body=bulk_data)
    assert res["errors"] is False

    chargeitem_data = _make_index_item("ChargeItem")
    bulk_data = [
        {
            "index": {
                "_id": _make_es_id(chargeitem_data, release_name, "ChargeItem"),
                "_index": index_name,
            }
        },
        chargeitem_data,
    ]
    res = conn.bulk(index=index_name, doc_type=_get_doc_type(), body=bulk_data)
    assert res["errors"] is False

    observation_data = _make_index_item("Observation")
    bulk_data = [
        {
            "index": {
                "_id": _make_es_id(observation_data, release_name, "Observation"),
                "_index": index_name,
            }
        },
        observation_data,
    ]
    res = conn.bulk(index=index_name, doc_type=_get_doc_type(), body=bulk_data)
    assert res["errors"] is False

    conn.indices.refresh(index=index_name)


async def _cleanup_es(conn, prefix=""):
    """RAW ES Connection"""
    aliases = await conn.cat.aliases()
    for alias in aliases.splitlines():
        name, index = alias.split()[:2]
        if name[0] == "." or index[0] == ".":
            # ignore indexes that start with .
            continue
        if name.startswith(prefix):
            try:
                await conn.indices.delete_alias(index, name)
                await conn.indices.delete(index)
            except elasticsearch.exceptions.AuthorizationException:
                pass
    indices = await conn.cat.indices()
    for index in indices.splitlines():
        _, _, index_name = index.split()[:3]
        if index_name[0] == ".":
            # ignore indexes that start with .
            continue
        if index_name.startswith(prefix):
            try:
                await conn.indices.delete(index_name)
            except elasticsearch.exceptions.AuthorizationException:
                pass
