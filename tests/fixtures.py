# _*_ coding: utf-8 _*_

import asyncio
import os
import pathlib
import sys
import typing

import pytest
from _pytest.monkeypatch import MonkeyPatch
from async_asgi_testclient import TestClient
from pytest_docker_fixtures import images

from hyperfhir.db.es import setup_elasticsearch

from ._utils import _cleanup_es

__author__ = "Md Nazrul Islam<email2nazrul@gmail.com>"

BASE_PATH = pathlib.Path(os.path.abspath(os.path.abspath(__file__))).parent.parent

images.configure(
    "elasticsearch",
    "docker.elastic.co/elasticsearch/elasticsearch",
    "7.9.3",
    env={
        "xpack.security.enabled": None,  # unset
        "discovery.type": "single-node",
        "http.host": "0.0.0.0",
        "transport.host": "127.0.0.1",
    },
    options={"ports": {"9200": "9222"}},
)

images.configure(
    "postgresql",
    image="postgres",
    version="12.4-alpine",
    env={
        "POSTGRES_USER": "test_hyperfhir_dm",
        "POSTGRES_PASSWORD": "MyPGSecretTest",
        "POSTGRES_HOST_AUTH_METHOD": "password",
        "POSTGRES_DB": "test_hyperfhir_db",
        "PGDATA": "/var/lib/postgresql/data/pgdata",
    },
    options={"ports": {"5432": "54329"}},
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def es_connection(es):
    """ """
    from hyperfhir.db.es import get_es_connection

    conn = get_es_connection()
    yield conn


@pytest.fixture(scope="session")
async def pg_connection(pg):
    """ """
    from hyperfhir.db import get_db

    db = get_db()
    # if not db.is_connected:
    #    await db.connect()
    yield db
    # if db.is_connected:
    #    await db.disconnect()


@pytest.fixture
async def es_setup(es_connection):
    """ """
    # do create index with other settings
    await setup_elasticsearch("R4", es_connection)
    await setup_elasticsearch("STU3", es_connection)
    # es connection, meta data of fixture, i.e id
    yield es_connection
    # clean up
    await _cleanup_es(es_connection.raw_connection)


@pytest.fixture(scope="session")
def monkeypatch() -> typing.Generator["MonkeyPatch", None, None]:
    """A convenient fixture for monkey-patching.

    The fixture provides these methods to modify objects, dictionaries or
    os.environ::

        monkeypatch.setattr(obj, name, value, raising=True)
        monkeypatch.delattr(obj, name, raising=True)
        monkeypatch.setitem(mapping, name, value)
        monkeypatch.delitem(obj, name, raising=True)
        monkeypatch.setenv(name, value, prepend=False)
        monkeypatch.delenv(name, raising=True)
        monkeypatch.syspath_prepend(path)
        monkeypatch.chdir(path)

    All modifications will be undone after the requesting test function or
    fixture has finished. The ``raising`` parameter determines if a KeyError
    or AttributeError will be raised if the set/deletion operation has no target.
    """
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope="session", autouse=True)
async def hyperfhir_site(pg, es):
    """ """
    from subprocess import check_call

    postgres_host, postgres_port = pg
    es_host, es_port = es

    check_call(["alembic", "upgrade", "head"], cwd=BASE_PATH)

    from hyperfhir.app import App

    client = TestClient(App)

    yield await client.__aenter__()

    await client.__aexit__(*sys.exc_info())
