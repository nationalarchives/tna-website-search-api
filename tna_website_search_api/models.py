from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, Protocol

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def _json_safe(value: object) -> bool:
    if value is None or isinstance(value, str | int | float | bool):
        return True
    if isinstance(value, list | tuple):
        return all(_json_safe(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _json_safe(item) for key, item in value.items())
    return False


@dataclass(frozen=True, slots=True)
class ParameterMetadata:
    name: str
    converter: str = "string"
    required: bool = True

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("parameter name must not be empty")

    def to_dict(self) -> dict[str, JsonValue]:
        return {"name": self.name, "converter": self.converter, "required": self.required}


@dataclass(frozen=True, slots=True)
class RouteMetadata:
    path: str
    methods: tuple[str, ...] | None = None
    parameters: tuple[ParameterMetadata, ...] = ()
    pattern_type: Literal["path", "regex"] = "path"
    methods_source: Literal["framework", "declared", "unknown"] = "unknown"
    subdomain: str | None = None
    host: str | None = None

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("route path must not be empty")
        if self.methods is not None:
            normalized = tuple(sorted({method.upper() for method in self.methods}))
            if not normalized or any(not method.isalpha() for method in normalized):
                raise ValueError("methods must contain valid HTTP method names")
            object.__setattr__(self, "methods", normalized)

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "path": self.path,
            "methods": list(self.methods) if self.methods is not None else None,
            "methods_source": self.methods_source,
            "parameters": [parameter.to_dict() for parameter in self.parameters],
            "pattern_type": self.pattern_type,
            "subdomain": self.subdomain,
            "host": self.host,
        }


@dataclass(frozen=True, slots=True)
class PageMetadata:
    id: str
    name: str
    framework: Literal["django", "flask", "custom"]
    routes: tuple[RouteMetadata, ...]
    title: str | None = None
    description: str | None = None
    tags: tuple[str, ...] = ()
    source: Literal["discovered", "registered"] = "discovered"
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.name:
            raise ValueError("page id and name must not be empty")
        if not self.routes:
            raise ValueError("a page must contain at least one route")
        if not _json_safe(self.metadata):
            raise ValueError("metadata must contain only JSON-safe values")
        object.__setattr__(self, "routes", tuple(sorted(self.routes, key=lambda route: route.path)))
        object.__setattr__(self, "tags", tuple(dict.fromkeys(self.tags)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "id": self.id,
            "name": self.name,
            "framework": self.framework,
            "routes": [route.to_dict() for route in self.routes],
            "title": self.title,
            "description": self.description,
            "tags": list(self.tags),
            "source": self.source,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CatalogMetadata:
    pages: tuple[PageMetadata, ...]

    def to_dict(self) -> dict[str, JsonValue]:
        return {"pages": [page.to_dict() for page in self.pages], "count": len(self.pages)}


class PageDiscoverer(Protocol):
    def discover(self) -> tuple[PageMetadata, ...]: ...
