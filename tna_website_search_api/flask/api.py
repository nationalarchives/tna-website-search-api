from tna_website_search_api.models import ApplicationPage
from tna_website_search_api.flask.config import WebsiteSearchAPIConfig

def discover_routes(app) -> list[ApplicationPage]:
    routes = []

    for rule in app.url_map.iter_rules():
        view = app.view_functions[rule.endpoint]
        if WebsiteSearchAPIConfig.INCLUDE_ROUTES_BY_DEFAULT:
            if hasattr(view, "__search_index__") and not view.__search_index__:
                continue
        else:
            if not hasattr(view, "__search_index__") or not view.__search_index__:
                continue
        routes.append(
            ApplicationPage(
                url=str(rule),
                title=getattr(view, "__page_title__", ""),
                description=getattr(view, "__page_description__", ""),
                teaser_image=getattr(view, "__teaser_image__", None),
                weighting=getattr(view, "__weighting__", 0),
                tags=getattr(view, "__tags__", []),
            )
        )
    return routes