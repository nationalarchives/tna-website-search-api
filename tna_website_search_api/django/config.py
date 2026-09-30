from django.conf import settings

DEFAULTS = {
    "EXCLUDED_ROUTE_PREFIXES": ("admin/", "static/", "__debug__/"),
    "INCLUDE_ROUTES_BY_DEFAULT": True,
    "WEBSITE_SEARCH_API_ENABLED": True,
    "WEBSITE_SEARCH_PAGE_PROVIDERS": (),
    "WEBSITE_SEARCH_APPLICATION_METADATA": {
        "title": "Application title",
        "version": "1.0.0",
        "description": "Application description",
        "base_url": "https://www.example.com/some-application-name",
        "type_label": None,
        "first_published_at": None,
        "last_published_at": None,
    },
}


def get_setting(name: str):
    return getattr(settings, name, DEFAULTS[name])
