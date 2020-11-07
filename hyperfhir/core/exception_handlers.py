from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

HTTP_400_FHIR_VALIDATION = 400
FHIR = False


async def fhir_request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # do your custom
    if not FHIR:
        return await request_validation_exception_handler(request, exc)

    return JSONResponse(
        status_code=HTTP_400_FHIR_VALIDATION,
        content={"detail": jsonable_encoder(exc.errors())},
    )
