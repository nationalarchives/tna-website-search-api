try:
    import flask as _flask
except ImportError as error:
    raise ImportError(
        "Flask support requires `pip install tna-website-search-api[flask]`"
    ) from error

from .discovery import discover_pages
from .extension import PageCatalog

__all__ = ["PageCatalog", "discover_pages"]
