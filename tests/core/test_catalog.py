import pytest

from tna_website_search_api import (
    DiscoveryPolicy,
    PageMetadata,
    PagePatch,
    PageRegistry,
    PageSelector,
    RegistryError,
    RouteMetadata,
    build_catalog,
    make_page_id,
)


def page(name: str, path: str, *, source: str = "discovered") -> PageMetadata:
    return PageMetadata(
        id=make_page_id("flask", name, path) if source == "discovered" else name,
        name=name,
        framework="flask" if source == "discovered" else "custom",
        routes=(RouteMetadata(path, ("GET",), methods_source="framework"),),
        source=source,
    )


def test_add_override_exclude_precedence() -> None:
    registry = PageRegistry()
    registry.add(page("extra", "/extra", source="registered"))
    registry.override(PageSelector(name="home"), PagePatch(title="Homepage", tags=("public",)))
    registry.exclude(PageSelector(name="private"))

    catalog = build_catalog([page("private", "/private"), page("home", "/")], registry)

    assert [item.name for item in catalog.pages] == ["extra", "home"]
    assert catalog.pages[1].title == "Homepage"
    assert catalog.to_dict()["count"] == 2


def test_stale_and_ambiguous_selectors_fail() -> None:
    registry = PageRegistry()
    registry.override(PageSelector(name="missing"), PagePatch(title="Missing"))
    with pytest.raises(RegistryError, match="matched no pages"):
        build_catalog([page("home", "/")], registry)

    registry = PageRegistry()
    registry.override(PageSelector(route="/shared"), PagePatch(title="Shared"))
    with pytest.raises(RegistryError, match="ambiguous"):
        build_catalog([page("first", "/shared"), page("second", "/shared")], registry)


def test_policy_defaults_and_explicit_include() -> None:
    policy = DiscoveryPolicy(include_paths=frozenset({"/api/public"}))
    assert not policy.includes(page("private-api", "/api/private"))
    assert policy.includes(page("public-api", "/api/public"))
    assert not policy.includes(page("catalog", "/api/pages"), package_owned=True)


def test_metadata_must_be_json_safe() -> None:
    with pytest.raises(ValueError, match="JSON-safe"):
        PageMetadata(
            id="bad",
            name="bad",
            framework="custom",
            routes=(RouteMetadata("/bad"),),
            metadata={"bad": object()},
        )