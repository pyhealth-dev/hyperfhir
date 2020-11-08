"""Special Response Class for FHIR"""
import typing

from fastapi.encoders import jsonable_encoder
from fhirpath.enums import FHIR_VERSION
from fhirpath.json import json_dumps
from pydantic import BaseModel
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send


def fallback_resource_type_callable():
    """Just Marker"""
    return None


class FHIRHttpResponse(Response):
    """https://www.hl7.org/fhir/http.html"""

    pretty: bool = False
    fhir_version: FHIR_VERSION = None

    def __init__(
        self,
        content: typing.Any = None,
        status_code: int = 200,
        headers: dict = None,
        media_type: str = None,
        background: BackgroundTask = None,
        pretty: bool = None,
        fhir_version: FHIR_VERSION = None,
        exclude_comments: bool = False,
        locked: bool = False,
    ) -> None:
        if pretty is not None:
            self.pretty = pretty

        if fhir_version is not None:
            self.fhir_version = fhir_version

        self.exclude_comments = exclude_comments
        self.locked = locked

        Response.__init__(
            self,
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        :param scope:
        :param receive:
        :param send:
        :return:
        """
        if "FHIR_REQUEST_ID" in scope:
            scope["headers"].append(
                (b"X-Request-Id", str(scope["FHIR_REQUEST_ID"]).encode())
            )

        await Response.__call__(self, scope=scope, receive=receive, send=send)


class FHIRHttpJsonResponse(FHIRHttpResponse):
    """https://www.hl7.org/fhir/http.html"""

    media_type: str = "application/fhir+json"

    def render(self, content: typing.Any) -> bytes:
        """ """
        params = {"return_bytes": True}
        if self.pretty:
            params.update({"indent": 2, "sort_keys": True})

        if isinstance(content, BaseModel):
            if (
                getattr(
                    content.__class__,
                    "get_resource_type",
                    fallback_resource_type_callable,
                )()
                is not None
            ):
                params["exclude_comments"] = self.exclude_comments
                result = content.json(**params)
                if typing.TYPE_CHECKING:
                    result = typing.cast(bytes, result)
                return result
            else:
                content = content.dict()

        return json_dumps(content, **params)


class FHIRHttpXMLResponse(FHIRHttpResponse):
    """https://www.hl7.org/fhir/http.html"""

    media_type: str = "application/fhir+xml"

    def render(self, content: typing.Dict[str, typing.Any]) -> bytes:
        """ """
        params = {"return_bytes": True}
        if self.pretty:
            params.update({"indent": 2, "sort_keys": True})
        # json to xml
        return json_dumps(content, **params)


def fhir_rest_response(
    request: Request,
    data: typing.Any,
    status_code: int = 200,
    headers: typing.Dict[str, str] = None,
):
    if not isinstance(data, BaseModel):
        data = jsonable_encoder(data)
    mime = request.scope.get(
        "FHIR_RESPONSE_FORMAT", request.scope["FHIR_RESPONSE_ACCEPT"]
    )
    if mime == "application/fhir+xml":
        resp_class = FHIRHttpXMLResponse
    else:
        resp_class = FHIRHttpJsonResponse
    response = resp_class(
        data,
        status_code=status_code,
        headers=headers,
        pretty=request.scope.get("FHIR_RESPONSE_PRETTY", None),
        fhir_version=request.scope["FHIR_VERSION"],
    )
    # xxx: do more for headers?
    return response
