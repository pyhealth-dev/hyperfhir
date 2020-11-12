import uuid
from datetime import datetime
from email.utils import format_datetime

from databases import Database
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fhir.resources.fhirtypes import BundleType, ResourceType
from fhirpath.search import SearchContext, fhir_search
from pydantic import ValidationError

from hyperfhir.api import tasks
from hyperfhir.api.deps import get_db, get_es_search_context
from hyperfhir.core.responses import fhir_rest_response
from hyperfhir.core.utils import fhir_resource_from_request
from hyperfhir.models import crud

__author__ = "Md Nazrul Islam <email2nazrul@gmail.com>"

router = APIRouter()


@router.get("/", response_model=BundleType, status_code=200)
async def search_all(resource_request: ResourceType, request: Request):
    """``GET [base]/[type]{?[parameters]{&_format=[mime-type]}}``
    This searches all resources of a particular type using the criteria represented in the parameters.
    Because of the way that some user agents and proxies treat GET and POST requests,
    in addition to the get based search method above, servers that support search SHALL also
    support a POST based search:
    POST  [base]/[type]/_search{?[parameters]{&_format=[mime-type]}}
    Content-Type: application/x-www-form-urlencoded
    param1=value&param2=value

    :param resource_request:
    :param request:
    :return:
    """
    return None


@router.post("/", response_model=BundleType, status_code=200)
async def batch(resource_request: BundleType, request: Request):
    """The batch and transaction interactions submit a set of actions
    to perform on a server in a single HTTP request/response.
    The actions may be performed independently as a "batch", or as a single atomic
    "transaction" where the entire set of changes succeed or fail as a single entity.
    Multiple actions on multiple resources of the same or different types may be submitted,
    and they may be a mix of other interactions defined on this page
    (e.g. read, search, create, update, delete, etc.), or using the operations framework.

    The transaction mode is especially useful where one would otherwise need multiple
    interactions, possibly with a risk of loss of referential integrity if a later interaction
    fails (e.g. when storing a Provenance resource and its corresponding target resource,
    or and IHE-MHD transaction "Provide Document Resources"  with a DocumentManifest, and some
    number of DocumentReference, List, and Binary resources).

    Note that transactions and conditional create/update/delete are complex interactions
    and it is not expected that every server will implement them. Servers that don't support
    the batches or transactions SHOULD return an HTTP 400 error and MAY include an OperationOutcome.

    A batch or transaction interaction is performed by an HTTP POST command as shown:

    ``POST [base] {?_format=[mime-type]}``
    The content of the post submission is a Bundle with Bundle.type = batch or transaction.
    Each entry SHALL carry request details (Bundle.entry.request) that provides the HTTP
    details of the action in order to inform the system processing the batch or transaction
    what to do for the entry. If the HTTP command is a PUT or POST, then the entry SHALL
    contain a resource for the body of the action. The resources in the bundle are each
    processed separately as if they were an individual interaction or operation as otherwise
    described on this page, or the Operations framework. The actions are subject to the normal
    processing for each, including the meta element, verification and version aware updates,
    and transactional integrity. In the case of a batch each entry is treated as if an individual
    interaction or operation, in the case of a transaction all interactions or operations either
    succeed or fail together (see below).
    :param resource_request:
    :param request:
    :return:
    """
    return None


@router.get("/metadata", status_code=200)
async def capabilities():
    pass


@router.get(
    "/_history",
    response_model=BundleType,
    status_code=200,
)
async def history_all(request: Request):
    pass


@router.post(
    "/_search",
    response_model=BundleType,
    status_code=200,
)
async def search_all_post(resource_request: ResourceType, request: Request):
    pass


@router.post("/{resource}", status_code=201)
async def create(
    resource: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db),
    search_context: SearchContext = Depends(get_es_search_context),
):
    """Headers to add
        1. Location: [base]/[type]/[id]/_history/[vid]
        2. Last-Modified:
        3. ETag:

    Conditional:
        1. No matches: The server processes the create as above
        2. One Match: The server ignores the post and returns 200 OK
        3. Multiple matches: The server returns a 412 Precondition Failed error
           indicating the client's criteria were not selective enough.

    Error Response Code:
        - 400 Bad Request - resource could not be parsed or failed basic FHIR validation rules
        - 404 Not Found - resource type not supported, or not a FHIR end-point
        - 422 Unprocessable Entity - the proposed resource violated applicable
          FHIR profiles or server business rules. This should be accompanied by an
          OperationOutcome resource providing additional detail.

    :param resource:
    :param request:
    :param db:
    :param background_tasks:
    :param search_context:
    :return:
    """
    # check Condition
    if request.scope.get("FHIR_CONDITION_NONE_EXIST"):
        # @see conditional section
        # fhir_search(search_context, params={})
        pass
    try:
        resource_obj = await fhir_resource_from_request(request, resource)
    except ValidationError as exc:
        print(exc)
        # xxx: do outcome report
        return
    # forced by system
    resource_obj.id = str(uuid.uuid4())
    resource_obj.meta = {"versionId": "1", "lastUpdated": datetime.utcnow()}

    # Insert into Database
    record = await crud.create_resource(
        db=db, resource=resource_obj, fhir_version=request.scope.get("FHIR_VERSION")
    )
    # Do Background TaskMQ
    # add history
    background_tasks.add_task(
        tasks.add_resource_history, db=db, record=record, first=True
    )
    # add ES
    background_tasks.add_task(
        tasks.add_elasticsearch_doc,
        es_engine=search_context.engine,
        record=record,
        create=True,
    )
    headers = {
        "Location": f"fhir/{resource}/{resource_obj.id}/_history/{resource_obj.meta.versionId}",
        "ETag": f'W/"{resource_obj.meta.versionId}"',
        "Last-Modified": format_datetime(resource_obj.meta.lastUpdated),
    }

    return fhir_rest_response(
        request, None, status_code=201, headers=headers, background=background_tasks
    )


@router.get(
    "/{resource}",
    response_model=BundleType,
    status_code=200,
)
async def search(resource: str, request: Request):
    pass


@router.get(
    "/{resource}/_history",
    response_model=BundleType,
    status_code=200,
)
async def history(resource: str, request: Request):
    return None
    # rsp = await fhir_rest_response()


@router.post(
    "/{resource}/_search",
    response_model=BundleType,
    status_code=200,
)
async def search_post(resource: str, request: Request):
    pass


@router.get(
    "/{resource}/{resource_id}",
    response_model=ResourceType,
    status_code=201,
)
async def read(resource_request: ResourceType, request: Request):
    """3.1.0.1.7 conditional read
    Clients may use the If-Modified-Since, or If-None-Match HTTP header on a read request. If so,
    they SHALL accept either a 304 Not Modified as a valid status code on the response
    (which means that the content is unchanged since that date) or
    full content (either the content has changed, or the server does not support conditional request).
    Servers can return 304 Not Modified where content is unchanged because the
    If-Modified-Since date-time or the If-None-Match ETag was specified, or they
    can return the full content as normal. This optimisation is relevant in
    reducing bandwidth for caching purposes and servers are encouraged but not
    required to support this. If servers don't support conditional read,
    they just return the full content.
    """
    pass


@router.delete("/{resource}/{resource_id}", status_code=204)
async def delete(resource_request: ResourceType, request: Request):
    pass


@router.patch(
    "/{resource}/{resource_id}",
    response_model=ResourceType,
    status_code=201,
)
async def patch(resource_request: ResourceType, request: Request):
    pass


@router.put(
    "/{resource}/{resource_id}",
    response_model=ResourceType,
    status_code=201,
)
async def update(resource_request: ResourceType, request: Request):
    pass


@router.get(
    "/{resource}/{resource_id}/_history",
    response_model=BundleType,
    status_code=200,
)
async def history_single(resource: str, resource_id: str):
    return {}


@router.get(
    "/{resource}/{resource_id}/_history/{vid}",
    response_model=ResourceType,
    status_code=200,
)
async def vread(resource: str, resource_id: str, vid: str):
    return None
