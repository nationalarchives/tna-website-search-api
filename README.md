# TNA Website Search API

Discover page-like routes in Django and Flask applications and expose normalized metadata through
a read-only JSON catalog. Application views are inspected but never invoked.

## Installation

```bash
pip install "tna-website-search-api[django]"
# or
pip install "tna-website-search-api[flask]"
```

The core package has no framework dependency. Python 3.12 or newer is required.

## Django

Create and mount a catalog explicitly in the application's URL configuration:

```python
from django.urls import include, path
from tna_website_search_api.django import DjangoPageCatalog

page_catalog = DjangoPageCatalog()

urlpatterns = [
	# Application routes...
	path("api/pages/", include((page_catalog.get_urls(), "page-catalog"))),
]
```

Function-based Django views do not declare their allowed methods in route metadata, so their
`methods` value is `null`. Class-based views report safely declared `http_method_names`.

For registration that should run after Django settings load, add provider callables and install the
adapter app to enable system checks:

```python
INSTALLED_APPS = [
	# ...
	"tna_website_search_api.django",
]

TNA_WEBSITE_SEARCH_API = {
	"PROVIDERS": ["my_app.search_pages.register_pages"],
}
```

Each provider accepts the catalog's `PageRegistry` and may add, override, or exclude pages.

## Flask

Initialize the extension inside an application factory. Discovery happens on the first catalog
request, so blueprints registered after `init_app()` are included.

```python
from flask import Flask
from tna_website_search_api.flask import PageCatalog

page_catalog = PageCatalog()

def create_app():
	app = Flask(__name__)
	page_catalog.init_app(app, url_prefix="/api/pages")
	# Register application blueprints...
	return app
```

## Additions and overrides

Use an isolated registry when an application needs custom entries:

```python
from tna_website_search_api import (
	PageMetadata,
	PagePatch,
	PageRegistry,
	PageSelector,
	RouteMetadata,
)

registry = PageRegistry()
registry.add(PageMetadata(
	id="help",
	name="help",
	framework="custom",
	routes=(RouteMetadata("/help", ("GET",)),),
	title="Help",
	source="registered",
))
registry.override(PageSelector(name="home"), PagePatch(title="Homepage"))
registry.exclude(PageSelector(name="private-account"))
```

Pass `registry=registry` to either integration. Selectors can target an exact ID, qualified name, or
route. Missing and ambiguous selectors fail instead of silently changing the wrong page.

## API

- `GET /api/pages/?offset=0&limit=50` returns page summaries and the total count.
- `GET /api/pages/<page-id>/` returns one page and all of its routes.
- `limit` is capped at 100.

Both integrations accept an `authorize` callback. It runs before discovery and returns a concealed
404 when access is denied. Responses use `Cache-Control: private, no-store` and do not enable CORS.

By default, discovery includes GET-capable routes and excludes conventional `/admin`, `/api`,
`/static`, and `/media` paths. A `DiscoveryPolicy` can add exact includes/excludes or a predicate.
Route discovery cannot determine whether a view is truly public, so protect the catalog and tighten
the policy when an application's URL topology is sensitive.

Version 1 publishes metadata only. It does not proxy, render, scrape, or execute views; infer
authentication; generate search documents; or load third-party entry-point plugins.