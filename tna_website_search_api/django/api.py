from django.http import JsonResponse
from django.urls import URLPattern, URLResolver, get_resolver, path
from django.utils.module_loading import import_string
from django.views.decorators.http import require_GET

from tna_website_search_api.decorators import not_searchable
from tna_website_search_api.django.config import get_setting
from tna_website_search_api.models import Application, ApplicationPage


def _unwrap_view(callback):
    # Class-based views expose the original class via .view_class; decorators may be applied to either.
    return getattr(callback, "view_class", callback)


def _iter_patterns(patterns, prefix: str = ""):
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            yield from _iter_patterns(pattern.url_patterns, prefix + str(pattern.pattern))
        elif isinstance(pattern, URLPattern):
            yield prefix + str(pattern.pattern), pattern.callback


def _get_attr(callback, name: str, default):
    view_class = _unwrap_view(callback)
    return getattr(callback, name, getattr(view_class, name, default))


def _is_excluded(url: str, excluded_prefixes: tuple[str, ...]) -> bool:
    return url.lstrip("/").startswith(excluded_prefixes)


def _provider_pages() -> list[ApplicationPage]:
    pages = []
    for provider in get_setting("WEBSITE_SEARCH_PAGE_PROVIDERS"):
        if isinstance(provider, str):
            provider = import_string(provider)
        pages.extend(ApplicationPage.model_validate(page) for page in provider())
    return pages


def discover_routes(urlconf=None) -> list[ApplicationPage]:
    include_by_default = get_setting("INCLUDE_ROUTES_BY_DEFAULT")
    excluded_prefixes = tuple(
        prefix.lstrip("/") for prefix in get_setting("EXCLUDED_ROUTE_PREFIXES") if prefix
    )
    routes = []

    for route, callback in _iter_patterns(get_resolver(urlconf).url_patterns):
        normalized_route = route.lstrip("^/").rstrip("$")
        if _is_excluded(normalized_route, excluded_prefixes):
            continue
        search_index = _get_attr(callback, "__search_index__", None)
        if include_by_default:
            if search_index is False:
                continue
        elif not search_index:
            continue
        routes.append(
            ApplicationPage(
                url="/" + normalized_route,
                title=_get_attr(callback, "__page_title__", ""),
                description=_get_attr(callback, "__page_description__", ""),
                teaser_image=_get_attr(callback, "__teaser_image__", None),
                weighting=_get_attr(callback, "__weighting__", 0),
                tags=_get_attr(callback, "__tags__", []),
            )
        )
    routes.extend(
        page
        for page in _provider_pages()
        if not _is_excluded(page.url, excluded_prefixes)
    )
    return routes


def display_application(urlconf=None) -> Application:
    return Application(
        **get_setting("WEBSITE_SEARCH_APPLICATION_METADATA"),
        pages=discover_routes(urlconf),
    )


def _request_urlconf(request):
    return getattr(request, "urlconf", None)


@not_searchable
@require_GET
def pages_view(request):
    return JsonResponse(
        [page.model_dump(mode="json") for page in discover_routes(_request_urlconf(request))],
        safe=False,
    )


@not_searchable
@require_GET
def application_view(request):
    return JsonResponse(display_application(_request_urlconf(request)).model_dump(mode="json"))


def get_urls() -> list:
    """
    Return the website search API URL patterns, e.g. path("api/", include(get_urls())).

    Returns an empty list when WEBSITE_SEARCH_API_ENABLED is False.
    """
    if not get_setting("WEBSITE_SEARCH_API_ENABLED"):
        return []
    return [
        path("pages", pages_view, name="website_search_api_pages"),
        path("application", application_view, name="website_search_api_application"),
    ]
