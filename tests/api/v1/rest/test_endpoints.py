import pytest
from starlette.routing import Match

from hyperfhir.api.v1.endpoints.fhir import rest
from hyperfhir.app import App


@pytest.mark.asyncio
def find_routes(app: App, path: str, method: str = "GET"):
    partial = None
    routes = list()
    scope = {"type": "http", "path": path, "method": method}
    for route in app.routes:
        # Determine if any route matches the incoming scope,
        # and hand over to the matching route if found.
        match, child_scope = route.matches(scope)
        if match == Match.FULL and scope["method"] in route.methods:
            routes.append(route)
        elif match == Match.PARTIAL and partial is None:
            if scope["method"] in route.methods:
                partial = route
                break
    if partial is not None:
        routes.append(partial)
    return routes


@pytest.mark.asyncio
async def test_history_endpoints(hyperfhir_site):
    """
    :param hyperfhir_site:
    :return:
    """
    client, app = hyperfhir_site
    routes = find_routes(app, "/api/v1/fhir/Organization/0998/_history", "GET")
    assert len(routes) == 1
    # test single resource with history
    assert routes[0].endpoint == rest.history_single

    routes = find_routes(app, "/api/v1/fhir/Organization/_history", "GET")
    # test resource search with history
    assert len(routes) == 2  # with read match.
    assert routes[0].endpoint == rest.history

    routes = find_routes(app, "/api/v1/fhir/_history", "GET")
    # test resource search with history
    assert len(routes) == 2  # with create matches.
    assert routes[0].endpoint == rest.history_all


@pytest.mark.asyncio
async def test_vread_endpoint(hyperfhir_site):
    """
    :param hyperfhir_site:
    :return:
    """
    client, app = hyperfhir_site
    routes = find_routes(
        app, "/api/v1/fhir/Organization/0908-090-9-09TH/_history/101", "GET"
    )
    assert len(routes) == 1
    assert routes[0].endpoint == rest.vread


@pytest.mark.asyncio
async def test_search_endpoints(hyperfhir_site):
    """
    :param hyperfhir_site:
    :return:
    """
    client, app = hyperfhir_site
    routes = find_routes(app, "/api/v1/fhir/_search", "POST")
    # with create
    assert len(routes) == 2
    # search all request POST
    assert routes[0].endpoint == rest.search_all_post

    routes = find_routes(app, "/api/v1/fhir/", "GET")
    assert len(routes) == 1
    # search all resource GET
    assert routes[0].endpoint == rest.search_all

    routes = find_routes(app, "/api/v1/fhir/Organization", "GET")
    # with batch
    assert len(routes) == 1
    # search all resource GET
    assert routes[0].endpoint == rest.search

    routes = find_routes(app, "/api/v1/fhir/Organization/_search", "POST")
    assert len(routes) == 1
    assert routes[0].endpoint == rest.search_post


@pytest.mark.asyncio
async def test_create_endpoint(hyperfhir_site):
    """
    :param hyperfhir_site:
    :return:
    """
    client, app = hyperfhir_site
    routes = find_routes(app, "/api/v1/fhir/Organization", "POST")
    assert len(routes) == 1
    # create
    assert routes[0].endpoint == rest.create


@pytest.mark.asyncio
async def test_delete_endpoint(hyperfhir_site):
    """
    :param hyperfhir_site:
    :return:
    """
    client, app = hyperfhir_site
    routes = find_routes(app, "/api/v1/fhir/Organization/011", "DELETE")
    assert len(routes) == 1
    # create
    assert routes[0].endpoint == rest.delete


@pytest.mark.asyncio
async def test_patch_endpoint(hyperfhir_site):
    """
    :param hyperfhir_site:
    :return:
    """
    client, app = hyperfhir_site
    routes = find_routes(app, "/api/v1/fhir/Organization/011", "PATCH")
    assert len(routes) == 1
    # create
    assert routes[0].endpoint == rest.patch


@pytest.mark.asyncio
async def test_put_endpoint(hyperfhir_site):
    """
    :param hyperfhir_site:
    :return:
    """
    client, app = hyperfhir_site
    routes = find_routes(app, "/api/v1/fhir/Organization/011", "PUT")
    assert len(routes) == 1
    # create
    assert routes[0].endpoint == rest.update


@pytest.mark.asyncio
async def test_read_endpoint(hyperfhir_site):
    """
    :param hyperfhir_site:
    :return:
    """
    client, app = hyperfhir_site
    routes = find_routes(app, "/api/v1/fhir/Organization/011", "GET")
    assert len(routes) == 1
    # create
    assert routes[0].endpoint == rest.read


@pytest.mark.asyncio
async def test_batch_endpoint(hyperfhir_site):
    """
    :param hyperfhir_site:
    :return:
    """
    client, app = hyperfhir_site
    routes = find_routes(app, "/api/v1/fhir/", "POST")
    assert len(routes) == 1
    # create
    assert routes[0].endpoint == rest.batch


@pytest.mark.asyncio
async def test_metadata_endpoint(hyperfhir_site):
    """
    :param hyperfhir_site:
    :return:
    """
    client, app = hyperfhir_site
    routes = find_routes(app, "/api/v1/fhir/metadata", "GET")
    assert len(routes) == 2
    # metadata
    assert routes[0].endpoint == rest.capabilities
