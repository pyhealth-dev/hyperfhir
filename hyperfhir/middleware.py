"""https://www.hl7.org/fhir/http.html
https://www.hl7.org/fhir/security.html
"""
import typing
import uuid
from ast import literal_eval
from email.utils import parsedate_to_datetime

from fhirpath.enums import FHIR_VERSION
from fhirpath.utils import lookup_fhir_class
from starlette.datastructures import Headers, QueryParams
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from hyperfhir.core.responses import FHIRHttpJsonResponse

__author__ = "Md Nazrul Islam <email2nazrul@gmail.com>"

DEFAULT_FHIR_VERSION = "4.0"
ALLOWED_ACCEPTS = {"application/fhir+xml", "application/fhir+json"}

MIME_FHIR_VERSION_MAP: typing.Dict[str, FHIR_VERSION] = {
    "4.0": FHIR_VERSION["R4"],
    "3.0": FHIR_VERSION["STU3"],
}


class FHIRHTTPRequestHandlerMiddleware:
    """Headers to take care:
        1. Accept: [application/fhir+json | application/fhir+json; fhirVersion=4.0.1]
        2. If-None-Exist: [search parameters]
        3. If-Modified-Since: [Sat, 02 Feb 2013 12:02:47 GMT]
        4. If-None-Match: [W/"<etag_value>"]
        5. If-Match: [W/"23"]

    QueryString to take care:
        1. _pretty: [true | false]
        2. _format: [mime type]
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # pragma: no cover
            await self.app(scope, receive, send)
            return

        params = QueryParams(scope.get("query_string", b""))
        headers = Headers(scope=scope)
        errors = list()

        FHIRHTTPRequestHandlerMiddleware.prepare_fhir_scopes(
            scope, headers, params, errors
        )

        if len(errors) > 0:
            response = FHIRHTTPRequestHandlerMiddleware.error_response(scope, errors)
            await response(scope, receive, send)
        else:
            await self.app(scope, receive, send)

    @staticmethod
    def prepare_fhir_scopes(
        scope: Scope,
        headers: Headers,
        params: QueryParams,
        errors: typing.List[typing.Any],
    ):
        # Generate Request ID
        scope["FHIR_REQUEST_ID"] = uuid.uuid4()

        # 1. Prepare Accept & FHIR Version
        # --------------------------------
        accept = headers.get("accept", None)
        if accept:
            parts = accept.split(";")
            accept = parts[0].strip()
            if accept in ("application/json", "text/json"):
                accept = "application/fhir+json"
            if accept in ALLOWED_ACCEPTS:
                scope["FHIR_RESPONSE_ACCEPT"] = accept
            else:
                errors.append(
                    {
                        "loc": "Header.Accept",
                        "msg": f"Accept mime '{accept}' is not supported.",
                        "original": headers.get("accept"),
                    }
                )
            if len(parts) > 1:
                version_str = None
                try:
                    name, version_str = parts[1].strip().split("=")
                    if name == "fhirVersion":
                        version = MIME_FHIR_VERSION_MAP[version_str]
                        scope["FHIR_VERSION"] = version
                        scope["FHIR_VERSION_ORIGINAL"] = version_str
                    else:
                        errors.append(
                            {
                                "loc": "Header.Accept",
                                "msg": "Invalid format of FHIR Version is provided in mime",
                                "original": headers.get("accept"),
                            }
                        )
                except KeyError:
                    errors.append(
                        {
                            "loc": "Header.Accept",
                            "msg": f"Unsupported FHIR Version '{version_str}' is provided in mime",
                            "original": headers.get("accept"),
                        }
                    )
                except ValueError:
                    errors.append(
                        {
                            "loc": "Header.Accept",
                            "msg": "Invalid format of FHIR Version is provided in mime",
                            "original": headers.get("accept"),
                        }
                    )
        else:
            scope["FHIR_RESPONSE_ACCEPT"] = "application/fhir+json"

        if (
            scope.get("FHIR_VERSION_ORIGINAL", None) is None
            and scope.get("FHIR_VERSION", None) is None
        ):
            scope["FHIR_VERSION"] = MIME_FHIR_VERSION_MAP[DEFAULT_FHIR_VERSION]

        # 2. Check Query String
        # ---------------------
        format_mime = params.get("_format", None)
        if format_mime is not None:
            if format_mime in ALLOWED_ACCEPTS:
                scope["FHIR_RESPONSE_FORMAT"] = format_mime
            else:
                errors.append(
                    {
                        "loc": "QueryString._format",
                        "msg": f"Format mime '{format_mime}' is not supported.",
                        "original": format_mime,
                    }
                )
        pretty_response = params.get("_pretty", None)
        if pretty_response is not None:
            if pretty_response in ("true", "false"):
                scope["FHIR_RESPONSE_PRETTY"] = pretty_response == "true"

            else:
                errors.append(
                    {
                        "loc": "QueryString._pretty",
                        "msg": f"Invalid ``_pretty`` value '{pretty_response}' is provided.",
                        "original": pretty_response,
                    }
                )

        # 3. Prepare Conditional Headers
        # ------------------------------
        if headers.get("If-None-Exist"):
            scope["FHIR_CONDITION_NONE_EXIST"] = [
                tuple(map(lambda x: x.strip(), headers.get("If-None-Exist").split("=")))
            ]

        if headers.get("If-Modified-Since"):
            try:
                scope["FHIR_CONDITION_MODIFIED_SINCE"] = parsedate_to_datetime(
                    headers.get("If-Modified-Since")
                )
            except ValueError:
                errors.append(
                    {
                        "loc": "Header.If-Modified-Since",
                        "msg": "Invalid formatted datetime value is provided.",
                        "original": headers.get("If-Modified-Since"),
                    }
                )
        if headers.get("If-None-Match"):
            try:
                scope["FHIR_CONDITION_NONE_MATCH"] = literal_eval(
                    headers.get("If-None-Match").replace("W/", "")
                )
            except (SyntaxError, ValueError):
                errors.append(
                    {
                        "loc": "Header.If-None-Match",
                        "msg": "Invalid formatted ETag value is provided.",
                        "original": headers.get("If-None-Match"),
                    }
                )

        if headers.get("If-Match"):
            try:
                scope["FHIR_CONDITION_MATCH"] = literal_eval(
                    headers.get("If-Match").replace("W/", "")
                )
            except (SyntaxError, ValueError):
                errors.append(
                    {
                        "loc": "Header.If-Match",
                        "msg": "Invalid formatted ETag value is provided.",
                        "original": headers.get("If-Match"),
                    }
                )

    @staticmethod
    def error_response(scope: Scope, errors) -> Response:
        default = MIME_FHIR_VERSION_MAP[DEFAULT_FHIR_VERSION]
        klass = lookup_fhir_class("OperationOutcome", fhir_release=default)
        issues = list()

        for error in errors:
            issue = {
                "severity": "fatal",
                "code": "value",
                "details": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/operation-outcome",
                            "code": "MSG_BAD_FORMAT",
                            "display": error["msg"],
                        }
                    ]
                },
                "diagnostics": f"Request loc: {error['loc']}, Original Value: {error['original']}",
            }
            issues.append(issue)

        outcome = klass(**{"id": str(scope["FHIR_REQUEST_ID"]), "issue": issues})

        return FHIRHttpJsonResponse(
            outcome, status_code=422, fhir_version=default, locked=True
        )
