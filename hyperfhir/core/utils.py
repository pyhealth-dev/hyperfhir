import typing

from fhirpath.utils import json_loads, lookup_fhir_class
from pydantic import BaseModel
from starlette.requests import Request


async def fhir_resource_from_request(request: Request, resource_type: str) -> BaseModel:
    """
    :param request:
    :param resource_type:
    :return:
    """
    raw = await request.body()
    klass = lookup_fhir_class(resource_type, request.scope["FHIR_VERSION"])
    obj = klass.parse_raw(raw)
    return obj


async def deserialize_json_request_body(
    request: Request,
) -> typing.Union[typing.Dict[str, typing.Any], typing.List[typing.Any]]:
    """ """
    raw = await request.body()
    return json_loads(raw)
