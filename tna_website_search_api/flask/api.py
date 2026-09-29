from flask import Blueprint, current_app, jsonify

from tna_website_search_api.models import ApplicationPage, Application
from tna_website_search_api.flask.config import WebsiteSearchAPIConfig
from tna_website_search_api.flask.decorators import not_searchable

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

def display_application(app) -> Application:
    return Application(
        **app.config["WEBSITE_SEARCH_APPLICATION_METADATA"],
        pages=discover_routes(app)
    )


bp = Blueprint("website_search_api", __name__)


@bp.get("/pages")
@not_searchable
def pages_view():
    return jsonify([page.model_dump(mode="json") for page in discover_routes(current_app)])

@bp.get("/application")
@not_searchable
def application_view():
    return jsonify(display_application(current_app).model_dump(mode="json"))


def register_api(app, url_prefix: str | None = None) -> None:
    """
    Register the website search API endpoint on a Flask app.

    url_prefix is used to add a prefix to the API endpoint URLs, for example url_prefix="our-application-route"
    would result in the API endpoint being available at "/our-application-route/api/pages".
    """
    if not WebsiteSearchAPIConfig.WEBSITE_SEARCH_API_ENABLED:
        return
    prefix = url_prefix.rstrip("/") if url_prefix else ""
    app.register_blueprint(bp, url_prefix=prefix + WebsiteSearchAPIConfig.WEBSITE_SEARCH_API_PREFIX)
