import os
from functools import lru_cache

from fhirpath.connectors.factory.es import AsyncElasticsearchConnection
from fhirpath.dialects.elasticsearch import ElasticSearchDialect
from fhirpath.engine.es import AsyncElasticsearchEngine
from fhirpath.utils import json_loads
from starlette.requests import Request

from hyperfhir.core.config import ELASTICSEARCH_STATIC_MAPPINGS

from ..core.config import get_elasticsearch_dsn

__author__ = "Md Nazrul Islam<email2nazrul@gmail.com>"

ES_CONN_ = None


def get_es_connection(
    url: str = None, create: bool = False
) -> AsyncElasticsearchConnection:
    """
    :param url:
    :param create:
    :return:
    """
    global ES_CONN_
    if ES_CONN_ is None or create is True:
        url = url or get_elasticsearch_dsn()
        ES_CONN_ = AsyncElasticsearchConnection.from_url(url)
    return ES_CONN_


@lru_cache(maxsize=None, typed=True)
def _get_index_name(release_name: str, resource_type: str = None):
    """ """
    prefix = f"fv_{release_name}"
    basename = os.environ.get("ELASTICSEARCH_INDEX_BASENAME")
    version = "1"
    return "_".join([prefix, basename, version]).lower()


@lru_cache(maxsize=1024, typed=True)
def _get_mapping(fhir_release: str, resource_type: str):
    """
    :param fhir_release:
    :param resource_type:
    :return:
    """
    filename = (
        ELASTICSEARCH_STATIC_MAPPINGS / fhir_release / f"{resource_type}.mapping.json"
    )
    try:
        with open(str(filename), "rb") as fp:
            return json_loads(fp.read())
    except FileNotFoundError:
        raise LookupError(
            f"No mapping has been found for {fhir_release}.{resource_type}"
        )


@lru_cache(maxsize=None)
def _get_doc_type():
    """ """
    doc_type = os.environ.get("ELASTICSEARCH_INDEX_DOCNAME", "_fhir_resource_doc")
    return doc_type.lower()


class ElasticsearchEngine(AsyncElasticsearchEngine):
    """ """

    def __init__(self, connection: AsyncElasticsearchConnection, request: Request):
        """
        :param connection:
        :param request:
        """
        self.request = request

        AsyncElasticsearchEngine.__init__(
            self,
            fhir_release=request.scope.get("FHIR_VERSION"),
            conn_factory=lambda x: connection,
            dialect_factory=lambda x: ElasticSearchDialect(connection),
        )

    def get_index_name(self, resource_type=None):
        """ """
        return _get_index_name(self.fhir_release.name, resource_type)

    def calculate_field_index_name(self, resource_type):
        """We use same as Resource Type Name"""
        return resource_type

    def get_mapping(self, resource_type):
        """ """
        return _get_mapping(self.fhir_release.name, resource_type)

    def current_url(self):
        """ """
        return self.request.url

    @staticmethod
    def get_doc_type():
        """ """
        return _get_doc_type()

    def extract_hits(self, selects, hits, container, doc_type=None):
        """ """
        doc_type = doc_type or ElasticsearchEngine.get_doc_type()
        return AsyncElasticsearchEngine.extract_hits(
            self, selects, hits, container, doc_type
        )


async def setup_elasticsearch(
    release_name: str,
    es_conn: AsyncElasticsearchConnection = None,
    create: bool = False,
):
    """
    :param release_name:
    :param es_conn:
    :param create:
    :return:
    """
    conn = es_conn.raw_connection
    real_index_name = _get_index_name(release_name)
    exist = await conn.indices.exists(real_index_name)
    if create is True:
        if exist:
            # xxx: es_conn.indices.delete_alias(real_index_name, alias_name="")
            await conn.indices.delete(real_index_name)
    else:
        if exist:
            return

    body = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "fhir_reference_analyzer": {
                        "tokenizer": "keyword",
                        "filter": ["fhir_reference_filter"],
                    },
                },
                "filter": {
                    "fhir_reference_filter": {
                        "type": "pattern_capture",
                        "preserve_original": True,
                        "patterns": [r"(?:\w+\/)?(https?\:\/\/.*|[a-zA-Z0-9_-]+)"],
                    },
                },
                "char_filter": {},
                "tokenizer": {},
            },
            "index": {
                "mapping": {
                    "total_fields": {
                        "limit": int(
                            os.environ.get(
                                "ELASTICSEARCH_INDEX_MAPPING_TOTAL_FIELDS", "5000"
                            )
                        )
                    },
                    "depth": {
                        "limit": int(
                            os.environ.get("ELASTICSEARCH_INDEX_MAPPING_DEPTH", "50")
                        )
                    },
                    "nested_fields": {
                        "limit": int(
                            os.environ.get(
                                "ELASTICSEARCH_INDEX_MAPPING_NESTED_FIELDS", "500"
                            )
                        )
                    },
                }
            },
        },
        "mappings": {
            "dynamic": False,
            "properties": {
                "access_roles": {"index": True, "store": True, "type": "keyword"},
                "access_users": {"index": True, "store": True, "type": "keyword"},
            },
        },
    }

    for jsonfile in (ELASTICSEARCH_STATIC_MAPPINGS / release_name).glob(
        "*.mapping.json"
    ):

        with open(str(jsonfile), "rb") as fp:
            data = json_loads(fp.read())
            body["mappings"]["properties"][data["resourceType"]] = data["mapping"]

    await conn.indices.create(real_index_name, body=body)
    # xxx: create alias
    await conn.indices.refresh(index=real_index_name)
