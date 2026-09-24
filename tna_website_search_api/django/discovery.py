from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, Literal

from django.urls import URLPattern, URLResolver, get_resolver
from django.urls.resolvers import RegexPattern, RoutePattern

from ..catalog import make_page_id
from ..models import PageMetadata, ParameterMetadata, RouteMetadata
from ..policy import DiscoveryPolicy

_PARAMETER = re.compile(r"<(?:(?P<converter>[^>:]+):)?(?P<name>[^>]+)>")


def _join(prefix: str, pattern: object) -> str:
    value = str(pattern)
    if value.startswith("^"):
        value = value[1:]
    value = value.removesuffix("\\Z").removesuffix("$")
    return f"/{prefix}{value}".replace("//", "/")


def _parameters(path: str) -> tuple[ParameterMetadata, ...]:
    return tuple(
        ParameterMetadata(match.group("name"), match.group("converter") or "string")
        for match in _PARAMETER.finditer(path)
    )


def _methods(
    callback: Any,
) -> tuple[tuple[str, ...] | None, Literal["declared", "unknown"]]:
    view_class = getattr(callback, "view_class", None)
    names = getattr(view_class, "http_method_names", None)
    if names is None:
        return None, "unknown"
    methods = tuple(name.upper() for name in names if name and name != "options")
    return methods or None, "declared"


def _walk(
    patterns: Iterable[URLPattern | URLResolver],
    *,
    prefix: str = "",
    namespaces: tuple[str, ...] = (),
    active: frozenset[int] = frozenset(),
) -> Iterable[PageMetadata]:
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            if id(pattern) in active:
                continue
            namespace = namespaces
            resolver_namespace = pattern.namespace
            if isinstance(resolver_namespace, str):
                namespace += (resolver_namespace,)
            yield from _walk(
                pattern.url_patterns,
                prefix=f"{prefix}{pattern.pattern}",
                namespaces=namespace,
                active=active | {id(pattern)},
            )
            continue

        path = _join(prefix, pattern.pattern)
        route_name = pattern.name if isinstance(pattern.name, str) else "unnamed"
        name = ":".join((*namespaces, route_name))
        methods, methods_source = _methods(pattern.callback)
        pattern_type: Literal["path", "regex"] = (
            "regex" if isinstance(pattern.pattern, RegexPattern) else "path"
        )
        route = RouteMetadata(
            path=path,
            methods=methods,
            methods_source=methods_source,
            parameters=_parameters(path) if isinstance(pattern.pattern, RoutePattern) else (),
            pattern_type=pattern_type,
        )
        yield PageMetadata(
            id=make_page_id("django", name, path),
            name=name,
            framework="django",
            routes=(route,),
        )


def discover_pages(
    *,
    urlconf: str | None = None,
    policy: DiscoveryPolicy | None = None,
) -> tuple[PageMetadata, ...]:
    selected_policy = policy or DiscoveryPolicy()
    discovered = _walk(get_resolver(urlconf).url_patterns)
    pages: dict[str, PageMetadata] = {}
    for page in discovered:
        if not selected_policy.includes(page):
            continue
        existing = pages.get(page.id)
        if existing is None:
            pages[page.id] = page
        elif page.routes[0] not in existing.routes:
            pages[page.id] = PageMetadata(
                id=existing.id,
                name=existing.name,
                framework="django",
                routes=existing.routes + page.routes,
            )
    return tuple(sorted(pages.values(), key=lambda page: (page.name, page.id)))
