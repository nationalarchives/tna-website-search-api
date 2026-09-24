from __future__ import annotations

import hashlib

from .models import CatalogMetadata, PageMetadata
from .registry import PageRegistry, RegistryError


def make_page_id(framework: str, name: str, route: str) -> str:
    digest = hashlib.sha256(f"{framework}\0{name}\0{route}".encode()).hexdigest()[:16]
    return f"{framework}-{digest}"


def build_catalog(
    discovered: tuple[PageMetadata, ...] | list[PageMetadata], registry: PageRegistry
) -> CatalogMetadata:
    snapshot = registry.snapshot()
    pages = [*discovered, *snapshot.additions]
    seen_ids: set[str] = set()
    for page in pages:
        if page.id in seen_ids:
            raise RegistryError(f"duplicate page id: {page.id}")
        seen_ids.add(page.id)

    for selector, patch in snapshot.overrides:
        matches = [index for index, page in enumerate(pages) if selector.matches(page)]
        if not matches:
            raise RegistryError(f"override selector matched no pages: {selector}")
        if len(matches) > 1 and not selector.many:
            raise RegistryError(f"override selector is ambiguous: {selector}")
        for index in matches:
            pages[index] = patch.apply(pages[index])

    for selector in snapshot.exclusions:
        matches = [page for page in pages if selector.matches(page)]
        if not matches:
            raise RegistryError(f"exclusion selector matched no pages: {selector}")
        if len(matches) > 1 and not selector.many:
            raise RegistryError(f"exclusion selector is ambiguous: {selector}")
        pages = [page for page in pages if not selector.matches(page)]

    return CatalogMetadata(tuple(sorted(pages, key=lambda page: (page.name, page.id))))
