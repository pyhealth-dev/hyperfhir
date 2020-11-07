from databases import Database
from fastapi import Depends
from fhirpath.connectors.factory.es import AsyncElasticsearchConnection
from starlette.requests import Request

from hyperfhir.db.es import get_es_connection
from hyperfhir.db.main import get_db


def get_es_engine(
    request: Request, es_conn: AsyncElasticsearchConnection = Depends(get_es_connection)
):
    """
    :param request:
    :param es_conn:
    :return:
    """
