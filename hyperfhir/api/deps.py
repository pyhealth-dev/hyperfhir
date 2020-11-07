from fastapi import Depends
from fhirpath.connectors.factory.es import AsyncElasticsearchConnection
from starlette.requests import Request

from hyperfhir.db.es import get_es_connection
from hyperfhir.db.main import get_db
from hyperfhir.db.es import ElasticsearchEngine
from fhirpath.search import SearchContext

__author__ = "Md Nazrul Islam<email2nazrul@gmail.com>"


def get_es_engine(
    request: Request, es_conn: AsyncElasticsearchConnection = Depends(get_es_connection)
) -> ElasticsearchEngine:
    """
    :param request:
    :param es_conn:
    :return:
    """
    return ElasticsearchEngine(connection=es_conn, request=request)


def get_es_search_context(
    resource: str, engine: ElasticsearchEngine = Depends(get_es_engine)
) -> SearchContext:
    """
    :param resource:
    :param engine:
    :return:
    """
    context = SearchContext(engine, resource_type=resource)
    return context


__all__ = ["get_db", "get_es_connection", "get_es_engine", "get_es_search_context"]
