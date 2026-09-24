from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .models import PageMetadata

PagePredicate = Callable[[PageMetadata], bool]


@dataclass(frozen=True, slots=True)
class DiscoveryPolicy:
    include_names: frozenset[str] = frozenset()
    include_paths: frozenset[str] = frozenset()
    exclude_names: frozenset[str] = frozenset()
    exclude_paths: frozenset[str] = frozenset()
    excluded_prefixes: tuple[str, ...] = ("/admin", "/api", "/static", "/media")
    predicate: PagePredicate | None = None

    def includes(self, page: PageMetadata, *, package_owned: bool = False) -> bool:
        if package_owned:
            return False
        paths = {route.path for route in page.routes}
        explicitly_included = page.name in self.include_names or bool(paths & self.include_paths)
        if page.name in self.exclude_names or paths & self.exclude_paths:
            return False
        if not explicitly_included and any(
            path == prefix or path.startswith(f"{prefix}/")
            for path in paths
            for prefix in self.excluded_prefixes
        ):
            return False
        if not explicitly_included and not any(
            route.methods is None or "GET" in route.methods for route in page.routes
        ):
            return False
        return self.predicate(page) if self.predicate is not None else True
