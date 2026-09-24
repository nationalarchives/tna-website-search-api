from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from typing import cast

from flask import Blueprint, Flask, Response, current_app, jsonify, request

from ..catalog import build_catalog
from ..models import CatalogMetadata
from ..policy import DiscoveryPolicy
from ..registry import PageRegistry, default_registry
from .discovery import discover_pages

Authorize = Callable[[], bool]
_EXTENSION_KEY = "tna_website_search_api"


@dataclass(slots=True)
class _State:
    registry: PageRegistry
    policy: DiscoveryPolicy
    authorize: Authorize | None
    lock: RLock
    cached: tuple[int, tuple[tuple[str, str], ...], CatalogMetadata] | None = None


def _secure(response: Response) -> Response:
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _state(app: Flask) -> _State:
    return cast(_State, app.extensions[_EXTENSION_KEY])


def _error(name: str, status: int) -> Response:
    response = jsonify(error=name)
    response.status_code = status
    return _secure(response)


def _catalog(app: Flask) -> CatalogMetadata:
    state = _state(app)
    signature = tuple(sorted((rule.endpoint, rule.rule) for rule in app.url_map.iter_rules()))
    revision = state.registry.revision
    with state.lock:
        if state.cached is not None and state.cached[:2] == (revision, signature):
            return state.cached[2]
        catalog = build_catalog(discover_pages(app, policy=state.policy), state.registry)
        state.cached = (revision, signature, catalog)
        return catalog


class PageCatalog:
    def init_app(
        self,
        app: Flask,
        *,
        registry: PageRegistry | None = None,
        policy: DiscoveryPolicy | None = None,
        authorize: Authorize | None = None,
        url_prefix: str = "/api/pages",
    ) -> None:
        if _EXTENSION_KEY in app.extensions:
            raise RuntimeError("PageCatalog is already installed on this application")
        app.extensions[_EXTENSION_KEY] = _State(
            registry or default_registry, policy or DiscoveryPolicy(), authorize, RLock()
        )
        blueprint = Blueprint("tna_website_search_api", __name__)

        @blueprint.get("/")
        def list_pages() -> Response:
            state = _state(current_app)
            if state.authorize is not None and not state.authorize():
                return _error("not_found", 404)
            try:
                offset = max(0, int(request.args.get("offset", "0")))
                limit = min(100, max(1, int(request.args.get("limit", "50"))))
            except ValueError:
                return _error("invalid_pagination", 400)
            catalog = _catalog(current_app)
            pages = catalog.pages[offset : offset + limit]
            response = jsonify(
                pages=[page.to_dict() for page in pages],
                count=len(catalog.pages),
                offset=offset,
                limit=limit,
            )
            return _secure(response)

        @blueprint.get("/<page_id>/")
        def page_detail(page_id: str) -> Response:
            state = _state(current_app)
            if state.authorize is not None and not state.authorize():
                return _error("not_found", 404)
            page = next((item for item in _catalog(current_app).pages if item.id == page_id), None)
            if page is None:
                return _error("not_found", 404)
            return _secure(jsonify(page.to_dict()))

        app.register_blueprint(blueprint, url_prefix=url_prefix.rstrip("/"))

    def refresh(self, app: Flask) -> None:
        state = _state(app)
        with state.lock:
            state.cached = None
