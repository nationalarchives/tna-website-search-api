from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import path
from django.utils.module_loading import import_string

from ..catalog import build_catalog
from ..models import CatalogMetadata
from ..policy import DiscoveryPolicy
from ..registry import PageRegistry, default_registry
from .discovery import discover_pages

Authorize = Callable[[HttpRequest], bool]


def _response(payload: dict[str, Any], status: int = 200) -> JsonResponse:
    response = JsonResponse(payload, status=status)
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


class DjangoPageCatalog:
    def __init__(
        self,
        *,
        registry: PageRegistry | None = None,
        policy: DiscoveryPolicy | None = None,
        authorize: Authorize | None = None,
        urlconf: str | None = None,
    ) -> None:
        self.registry = registry or default_registry
        self.policy = policy or DiscoveryPolicy()
        self.authorize = authorize
        self.urlconf = urlconf
        self._cached: tuple[int, CatalogMetadata] | None = None
        self._providers_loaded = False
        self._lock = RLock()

    def refresh(self) -> None:
        with self._lock:
            self._cached = None

    def get_catalog(self) -> CatalogMetadata:
        with self._lock:
            if not self._providers_loaded:
                configuration = getattr(settings, "TNA_WEBSITE_SEARCH_API", {})
                for provider_path in configuration.get("PROVIDERS", ()):
                    provider = import_string(provider_path)
                    provider(self.registry)
                self._providers_loaded = True
            revision = self.registry.revision
            if self._cached is not None and self._cached[0] == revision:
                return self._cached[1]
            catalog = build_catalog(
                discover_pages(urlconf=self.urlconf, policy=self.policy), self.registry
            )
            self._cached = (revision, catalog)
            return catalog

    def _allowed(self, request: HttpRequest) -> bool:
        return self.authorize(request) if self.authorize is not None else True

    def list_view(self, request: HttpRequest) -> HttpResponse:
        if request.method not in {"GET", "HEAD"}:
            return _response({"error": "method_not_allowed"}, 405)
        if not self._allowed(request):
            return _response({"error": "not_found"}, 404)
        try:
            offset = max(0, int(request.GET.get("offset", "0")))
            limit = min(100, max(1, int(request.GET.get("limit", "50"))))
        except ValueError:
            return _response({"error": "invalid_pagination"}, 400)
        catalog = self.get_catalog()
        pages = catalog.pages[offset : offset + limit]
        return _response(
            {
                "pages": [page.to_dict() for page in pages],
                "count": len(catalog.pages),
                "offset": offset,
                "limit": limit,
            }
        )

    def detail_view(self, request: HttpRequest, page_id: str) -> HttpResponse:
        if request.method not in {"GET", "HEAD"}:
            return _response({"error": "method_not_allowed"}, 405)
        if not self._allowed(request):
            return _response({"error": "not_found"}, 404)
        page = next((item for item in self.get_catalog().pages if item.id == page_id), None)
        if page is None:
            return _response({"error": "not_found"}, 404)
        return _response(page.to_dict())

    def get_urls(self) -> list[Any]:
        return [
            path("", self.list_view, name="page-catalog"),
            path("<str:page_id>/", self.detail_view, name="page-detail"),
        ]
