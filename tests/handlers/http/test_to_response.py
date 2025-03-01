from json import loads
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

import pytest
from pydantic import ValidationError
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from starlette.responses import Response as StarletteResponse
from starlette.responses import StreamingResponse
from starlette.status import HTTP_200_OK

from starlite import (
    File,
    HttpMethod,
    HTTPRoute,
    MediaType,
    Redirect,
    Response,
    Stream,
    get,
    route,
)
from starlite.signature import SignatureModelFactory
from starlite.testing import create_test_client
from tests import Person, PersonFactory

if TYPE_CHECKING:
    from typing_extensions import AsyncGenerator


@pytest.mark.asyncio
async def test_to_response_async_await() -> None:
    @route(http_method=HttpMethod.POST, path="/person")
    async def test_function(data: Person) -> Person:
        assert isinstance(data, Person)
        return data

    person_instance = PersonFactory.build()
    test_function.signature_model = SignatureModelFactory(test_function.fn, [], set()).model()  # type:ignore[arg-type]

    response = await test_function.to_response(
        data=test_function.fn(data=person_instance), plugins=[], app=None  # type: ignore
    )
    assert loads(response.body) == person_instance.dict()


async def slow_numbers(minimum: int, maximum: int) -> Any:
    yield ("<html><body><ul>")
    for number in range(minimum, maximum + 1):
        yield "<li>%d</li>" % number
    yield ("</ul></body></html>")


generator = slow_numbers(1, 10)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected_response",
    [
        Response(status_code=HTTP_200_OK, content=b"abc", media_type=MediaType.TEXT),
        StarletteResponse(status_code=HTTP_200_OK, content=b"abc"),
        PlainTextResponse(content="abc"),
        HTMLResponse(content="<div><span/></div"),
        JSONResponse(status_code=HTTP_200_OK, content={}),
        RedirectResponse(url="/person"),
        StreamingResponse(status_code=HTTP_200_OK, content=generator),
        FileResponse("./test_to_response.py"),
    ],
)
async def test_to_response_returning_redirect_starlette_response(expected_response: StarletteResponse) -> None:
    @get(path="/test")
    def test_function() -> StarletteResponse:
        return expected_response

    with create_test_client(test_function) as client:
        http_route: HTTPRoute = client.app.routes[0]  # type: ignore
        route_handler = http_route.route_handlers[0]
        response = await route_handler.to_response(data=route_handler.fn(), plugins=[], app=None)  # type: ignore
        assert isinstance(response, StarletteResponse)
        assert response is expected_response


@pytest.mark.asyncio
async def test_to_response_returning_redirect_response() -> None:
    @get(path="/test", status_code=301)
    def test_function() -> Redirect:
        return Redirect(path="/somewhere-else")

    with create_test_client(test_function) as client:
        route: HTTPRoute = client.app.routes[0]  # type: ignore
        route_handler = route.route_handlers[0]
        response = await route_handler.to_response(data=route_handler.fn(), plugins=[], app=None)  # type: ignore
        assert isinstance(response, RedirectResponse)
        assert response.headers["location"] == "/somewhere-else"


@pytest.mark.asyncio
async def test_to_response_returning_file_response() -> None:
    current_file_path = Path(__file__).resolve()
    filename = Path(__file__).name

    @get(path="/test")
    def test_function() -> File:
        return File(path=current_file_path, filename=filename)

    with create_test_client(test_function) as client:
        route: HTTPRoute = client.app.routes[0]  # type: ignore
        route_handler = route.route_handlers[0]
        response = await route_handler.to_response(data=route_handler.fn(), plugins=[], app=None)  # type: ignore
        assert isinstance(response, FileResponse)
        assert response.stat_result


def my_iterator() -> Generator[int, None, None]:
    count = 0
    while True:
        count += 1
        yield count


async def my_async_iterator() -> "AsyncGenerator[int, None]":
    count = 0
    while True:
        count += 1
        yield count


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "iterator, should_raise", [[my_iterator(), False], [my_async_iterator(), False], [{"key": 1}, True]]
)
async def test_to_response_streaming_response(iterator: Any, should_raise: bool) -> None:
    if not should_raise:

        @get(path="/test")
        def test_function() -> Stream:
            return Stream(iterator=iterator)

        with create_test_client(test_function) as client:
            route: HTTPRoute = client.app.routes[0]  # type: ignore
            route_handler = route.route_handlers[0]
            response = await route_handler.to_response(data=route_handler.fn(), plugins=[], app=None)  # type: ignore
            assert isinstance(response, StreamingResponse)
    else:
        with pytest.raises(ValidationError):
            Stream(iterator=iterator)
