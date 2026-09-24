try:
    import django as _django
except ImportError as error:
    raise ImportError(
        "Django support requires `pip install tna-website-search-api[django]`"
    ) from error

from .discovery import discover_pages
from .integration import DjangoPageCatalog

__all__ = ["DjangoPageCatalog", "discover_pages"]
