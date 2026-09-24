import json

import pytest
from django.http import HttpResponse
from django.test import Client, override_settings
from django.urls import include, path

from tna_website_search_api import PageMetadata, PageRegistry, RouteMetadata
from tna_website_search_api.django import DjangoPageCatalog

pytestmark = pytest.mark.django_db

called = False


def home(request):
    global called
    called = True
    return HttpResponse("home")


catalog = DjangoPageCatalog(urlconf=__name__)
child_patterns = [path("item/<int:item_id>/", home, name="item")]
urlpatterns = [
    path("", home, name="home"),
    path("nested/", include((child_patterns, "child"), namespace="child")),
    path("api/pages/", include((catalog.get_urls(), "page-catalog"))),
]


@override_settings(ROOT_URLCONF=__name__)
def test_discovers_nested_urls_without_calling_views() -> None:
    global called
    called = False
    response = Client().get("/api/pages/")
    payload = json.loads(response.content)

    assert response.status_code == 200
    assert {page["name"] for page in payload["pages"]} == {"child:item", "home"}
    assert called is False
    assert response["Cache-Control"] == "private, no-store"


def provide_extra_page(registry: PageRegistry) -> None:
    registry.add(
        PageMetadata(
            id="extra",
            name="extra",
            framework="custom",
            routes=(RouteMetadata("/extra", ("GET",)),),
            source="registered",
        )
    )


@override_settings(
    ROOT_URLCONF=__name__,
    TNA_WEBSITE_SEARCH_API={"PROVIDERS": [f"{__name__}.provide_extra_page"]},
)
def test_provider_detail_and_authorization() -> None:
    protected = DjangoPageCatalog(
        registry=PageRegistry(),
        urlconf=__name__,
        authorize=lambda request: request.GET.get("key") == "ok",
    )
    denied = protected.list_view(Client().request().wsgi_request)
    assert denied.status_code == 404

    response = protected.detail_view(Client().get("/?key=ok").wsgi_request, "extra")
    assert response.status_code == 200
    assert json.loads(response.content)["name"] == "extra"
