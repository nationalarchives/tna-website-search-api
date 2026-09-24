from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from threading import RLock
from typing import Any

from .models import JsonValue, PageMetadata, RouteMetadata


class RegistryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PageSelector:
    id: str | None = None
    name: str | None = None
    route: str | None = None
    many: bool = False

    def __post_init__(self) -> None:
        if sum(value is not None for value in (self.id, self.name, self.route)) != 1:
            raise ValueError("a selector must set exactly one of id, name, or route")

    def matches(self, page: PageMetadata) -> bool:
        if self.id is not None:
            return page.id == self.id
        if self.name is not None:
            return page.name == self.name
        return any(route.path == self.route for route in page.routes)


@dataclass(frozen=True, slots=True)
class PagePatch:
    title: str | None = None
    description: str | None = None
    tags: tuple[str, ...] | None = None
    routes: tuple[RouteMetadata, ...] | None = None
    metadata: Mapping[str, JsonValue] | None = None

    def apply(self, page: PageMetadata) -> PageMetadata:
        changes: dict[str, Any] = {}
        for field_name in ("title", "description", "tags", "routes", "metadata"):
            value = getattr(self, field_name)
            if value is not None:
                changes[field_name] = value
        return replace(page, **changes)


@dataclass(frozen=True, slots=True)
class RegistrySnapshot:
    additions: tuple[PageMetadata, ...]
    overrides: tuple[tuple[PageSelector, PagePatch], ...]
    exclusions: tuple[PageSelector, ...]
    revision: int


class PageRegistry:
    def __init__(self) -> None:
        self._additions: list[PageMetadata] = []
        self._overrides: list[tuple[PageSelector, PagePatch]] = []
        self._exclusions: list[PageSelector] = []
        self._revision = 0
        self._lock = RLock()

    @property
    def revision(self) -> int:
        with self._lock:
            return self._revision

    def add(self, page: PageMetadata) -> None:
        if page.source != "registered":
            raise RegistryError("registered additions must use source='registered'")
        with self._lock:
            if any(existing.id == page.id for existing in self._additions):
                raise RegistryError(f"duplicate registered page id: {page.id}")
            self._additions.append(page)
            self._revision += 1

    def override(self, selector: PageSelector, patch: PagePatch) -> None:
        with self._lock:
            if any(existing == selector for existing, _ in self._overrides):
                raise RegistryError(f"duplicate override selector: {selector}")
            self._overrides.append((selector, patch))
            self._revision += 1

    def exclude(self, selector: PageSelector) -> None:
        with self._lock:
            if selector in self._exclusions:
                raise RegistryError(f"duplicate exclusion selector: {selector}")
            self._exclusions.append(selector)
            self._revision += 1

    def snapshot(self) -> RegistrySnapshot:
        with self._lock:
            return RegistrySnapshot(
                additions=tuple(self._additions),
                overrides=tuple(self._overrides),
                exclusions=tuple(self._exclusions),
                revision=self._revision,
            )


default_registry = PageRegistry()
