from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse
from .responses import fhir_rest_response
from fhirpath.utils import lookup_fhir_class

HTTP_400_FHIR_VALIDATION = 400
FHIR = False


async def fhir_request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # do your custom
    # identify as FHIR service
    # create FHIR outcome
    # response
    if "FHIR_REQUEST_ID" not in request.scope:
        # no dealings with no FHIR service
        return await request_validation_exception_handler(request, exc)

    # create operation outcome
    outcome = make_outcome(request, exc)

    return fhir_rest_response(
        request,
        outcome,
        status_code=request.scope.get("http_error_code", HTTP_400_FHIR_VALIDATION),
    )


def make_outcome(request: Request, exc: RequestValidationError):
    """
    https://terminology.hl7.org/2.0.0/CodeSystem-operation-outcome.html
    :param exc:
    :param status_code:
    :return:
    """
    klass = lookup_fhir_class(
        "OperationOutcome", fhir_release=request.scope["FHIR_VERSION"]
    )
    issues = list()
    for error in exc.errors():
        issue = {
            "severity": "error",
            "code": exc.code,
            "details": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/operation-outcome",
                        "code": exc.system_code,
                        "display": exc.body,
                    }
                ]
            },
            "diagnostics": f"loc: {error['loc']}, message: {error['msg']}",
        }
        issues.append(issue)

    outcome = klass(**{"id": str(request.scope["FHIR_REQUEST_ID"]), "issue": issues})
    return outcome
