from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import urlencode

from openapi_schema_pydantic.v3.v3_1_0.contact import Contact
from openapi_schema_pydantic.v3.v3_1_0.external_documentation import (
    ExternalDocumentation,
)
from openapi_schema_pydantic.v3.v3_1_0.info import Info
from openapi_schema_pydantic.v3.v3_1_0.license import License
from openapi_schema_pydantic.v3.v3_1_0.open_api import OpenAPI
from openapi_schema_pydantic.v3.v3_1_0.path_item import PathItem
from openapi_schema_pydantic.v3.v3_1_0.reference import Reference
from openapi_schema_pydantic.v3.v3_1_0.security_requirement import SecurityRequirement
from openapi_schema_pydantic.v3.v3_1_0.server import Server
from openapi_schema_pydantic.v3.v3_1_0.tag import Tag
from pydantic import AnyUrl, BaseModel, DirectoryPath, constr
from typing_extensions import Type

from starlite.cache import CacheBackendProtocol, SimpleCacheBackend
from starlite.openapi.controller import OpenAPIController
from starlite.template import TemplateEngineProtocol
from starlite.types import CacheKeyBuilder

if TYPE_CHECKING:
    from starlite.connection import Request


class CORSConfig(BaseModel):
    allow_origins: list[str] = ["*"]
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]
    allow_credentials: bool = False
    allow_origin_regex: str | None = None
    expose_headers: list[str] = []
    max_age: int = 600


class GZIPConfig(BaseModel):
    minimum_size: int = 500
    compresslevel: int = 9


class OpenAPIConfig(BaseModel):
    """Class containing Settings and Schema Properties"""

    create_examples: bool = False
    openapi_controller: Type[OpenAPIController] = OpenAPIController

    title: str
    version: str
    contact: Contact | None = None
    description: str | None = None
    external_docs: ExternalDocumentation | None = None
    license: License | None = None
    security: list[SecurityRequirement] | None = None
    servers: list[Server] = [Server(url="/")]
    summary: str | None = None
    tags: list[Tag] | None = None
    terms_of_service: AnyUrl | None = None
    webhooks: dict[str, PathItem | Reference] | None = None

    def to_openapi_schema(self) -> OpenAPI:
        """Generates an OpenAPI model"""
        return OpenAPI(
            externalDocs=self.external_docs,
            security=self.security,
            servers=self.servers,
            tags=self.tags,
            webhooks=self.webhooks,
            info=Info(
                title=self.title,
                version=self.version,
                description=self.description,
                contact=self.contact,
                license=self.license,
                summary=self.summary,
                termsOfService=self.terms_of_service,
            ),
        )


class StaticFilesConfig(BaseModel):
    path: constr(min_length=1)  # type: ignore
    directories: list[DirectoryPath]
    html_mode: bool = False


class TemplateConfig(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    directory: DirectoryPath | list[DirectoryPath]
    engine: Type[TemplateEngineProtocol]
    engine_callback: Callable[[Any], Any] | None


def default_cache_key_builder(request: Request) -> str:
    """
    Given a request object, returns a cache key by combining the path with the sorted query params
    """
    qp: list[tuple[str, Any]] = list(request.query_params.items())
    qp.sort(key=lambda x: x[0])
    return request.url.path + urlencode(qp, doseq=True)


class CacheConfig(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    backend: CacheBackendProtocol = SimpleCacheBackend()
    expiration: int = 60  # value in seconds
    cache_key_builder: CacheKeyBuilder = default_cache_key_builder
