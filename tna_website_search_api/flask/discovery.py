from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from flask import Flask

from ..catalog import make_page_id
from ..models import PageMetadata, ParameterMetadata, RouteMetadata
from ..policy import DiscoveryPolicy

_PARAMETER = re.compile(r"<(?:(?P<converter>[^>:()]+)(?:\([^>]*\))?:)?(?P<name>[^>]+)>")


def _parameters(rule: str, arguments: set[str]) -> tuple[ParameterMetadata, ...]:
    converters = {
        match.group("name"): match.group("converter") or "string"
        for match in _PARAMETER.finditer(rule)
    }
    return tuple(
        ParameterMetadata(name, converters.get(name, "unknown")) for name in sorted(arguments)
    )


def discover_pages(
    app: Flask, *, policy: DiscoveryPolicy | None = None
) -> tuple[PageMetadata, ...]:
    selected_policy = policy or DiscoveryPolicy()
    grouped: dict[str, list[Any]] = defaultdict(list)
    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        if (
            not isinstance(endpoint, str)
            or endpoint not in app.view_functions
            or rule.build_only
            or rule.redirect_to is not None
            or rule.alias
            or getattr(rule, "websocket", False)
        ):
            continue
        grouped[endpoint].append(rule)

    pages: list[PageMetadata] = []
    for endpoint, rules in grouped.items():
        routes = tuple(
            RouteMetadata(
                path=rule.rule,
                methods=tuple(rule.methods or ()),
                methods_source="framework",
                parameters=_parameters(rule.rule, set(rule.arguments)),
                subdomain=rule.subdomain or None,
                host=rule.host,
            )
            for rule in rules
        )
        page = PageMetadata(
            id=make_page_id("flask", endpoint, min(route.path for route in routes)),
            name=endpoint,
            framework="flask",
            routes=routes,
        )
        if selected_policy.includes(
            page, package_owned=endpoint.startswith("tna_website_search_api.")
        ):
            pages.append(page)
    return tuple(sorted(pages, key=lambda page: (page.name, page.id)))
