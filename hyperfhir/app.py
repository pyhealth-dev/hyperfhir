"""FastAPI APP"""
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from hyperfhir.api.v1.routes import api_router
from hyperfhir.core import config
from hyperfhir.core.exception_handlers import fhir_request_validation_exception_handler
from hyperfhir.db import get_db, get_es_connection
from hyperfhir.middleware import FHIRHTTPRequestHandlerMiddleware

App = FastAPI(title=config.PROJECT_NAME, openapi_url="/api/v1/openapi.json")
App.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["127.0.0.1"])
App.add_middleware(FHIRHTTPRequestHandlerMiddleware)
App.include_router(api_router, prefix="/api/v1")

# Custom overridden request validation handler
App.exception_handler(RequestValidationError)(fhir_request_validation_exception_handler)


@App.on_event("startup")
async def startup():
    """ """
    await get_db().connect()
    # Elasticsearch Connectivity Checking
    es_ping = await get_es_connection().raw_connection.ping()
    assert es_ping is True


@App.on_event("shutdown")
async def shutdown():
    """ """
    await get_db().disconnect()
    # close connection
    await get_es_connection().raw_connection.close()
