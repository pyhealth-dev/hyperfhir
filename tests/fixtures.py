# _*_ coding: utf-8 _*_

import sys
import asyncio
import pytest
import os
from pytest_docker_fixtures import images
import tempfile
from _pytest.monkeypatch import MonkeyPatch
from fhirpath.connectors import create_connection
from fhirpath.utils import proxy
from async_asgi_testclient import TestClient
from ._utils import TestElasticsearchEngine
from ._utils import _cleanup_es
from ._utils import _load_es_data
from ._utils import _setup_es_index
import typing
import os
import pathlib

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
    host, port = es
    conn_str = "es://@{0}:{1}/".format(host, port)
    conn = create_connection(conn_str, "elasticsearch.Elasticsearch")
    assert conn.raw_connection.ping()
    yield conn


@pytest.fixture(scope="session")
def engine(es_connection):
    """ """
    engine = TestElasticsearchEngine(es_connection)
    yield proxy(engine)


@pytest.fixture
def es_data(es_connection):
    """ """
    # do create index with other settings
    _setup_es_index(es_connection)
    _load_es_data(es_connection)

    # es connection, meta data of fixture, i.e id
    yield es_connection, None
    # clean up
    _cleanup_es(es_connection.raw_connection)


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
