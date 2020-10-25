# _*_ coding: utf-8 _*_

import os

import pytest
from pytest_docker_fixtures import images

from fhirpath.connectors import create_connection
from fhirpath.utils import proxy
from fastapi.testclient import TestClient
from hyperfhir.app import App
from ._utils import TestElasticsearchEngine
from ._utils import _cleanup_es
from ._utils import _load_es_data
from ._utils import _setup_es_index


__author__ = "Md Nazrul Islam<email2nazrul@gmail.com>"


images.configure(
    "elasticsearch",
    "docker.elastic.co/elasticsearch/elasticsearch",
    "7.3.1",
    env={
        "xpack.security.enabled": None,  # unset
        "discovery.type": "single-node",
        "http.host": "0.0.0.0",
        "transport.host": "127.0.0.1",
    },
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
    options={"ports": {"54329": "5432"}},
)


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
def hyperfhir_site():
    """ """
    client = TestClient(App)
    yield client, client.app
