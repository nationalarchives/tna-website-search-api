from flask import Blueprint, Flask

from tna_website_search_api import PagePatch, PageRegistry, PageSelector
from tna_website_search_api.flask import PageCatalog


def test_factory_discovery_and_catalog_exclusion() -> None:
    called = False
    app = Flask(__name__)
    catalog = PageCatalog()
    catalog.init_app(app)
    pages = Blueprint("pages", __name__)

    @pages.get("/article/<int:article_id>/")
    def article(article_id: int) -> str:
        nonlocal called
        called = True
        return str(article_id)

    app.register_blueprint(pages)
    response = app.test_client().get("/api/pages/")
    payload = response.get_json()

    assert response.status_code == 200
    assert [page["name"] for page in payload["pages"]] == ["pages.article"]
    assert payload["pages"][0]["routes"][0]["parameters"] == [
        {"converter": "int", "name": "article_id", "required": True}
    ]
    assert called is False
    assert response.headers["Cache-Control"] == "private, no-store"


def test_override_detail_authorization_and_duplicate_install() -> None:
    app = Flask(__name__)

    @app.get("/")
    def home() -> str:
        return "home"

    registry = PageRegistry()
    registry.override(PageSelector(name="home"), PagePatch(title="Homepage"))
    catalog = PageCatalog()
    catalog.init_app(app, registry=registry, authorize=lambda: True)

    with app.test_client() as client:
        listing = client.get("/api/pages/").get_json()
        page_id = listing["pages"][0]["id"]
        detail = client.get(f"/api/pages/{page_id}/")
    assert detail.status_code == 200
    assert detail.get_json()["title"] == "Homepage"

    try:
        catalog.init_app(app)
    except RuntimeError as error:
        assert "already installed" in str(error)
    else:
        raise AssertionError("duplicate installation must fail")

    denied_app = Flask("denied")
    PageCatalog().init_app(denied_app, authorize=lambda: False)
    assert denied_app.test_client().get("/api/pages/").status_code == 404