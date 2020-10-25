from fastapi import APIRouter

from .endpoints.fhir import rest

api_router = APIRouter()
api_router.include_router(rest.router, prefix="/fhir", tags=["fhir, rest"])
