def not_searchable(view) -> callable:
    """
    Flask decorator to denote a view/route as "not searchable", which will exclude it from the API.

    To be used in conjunction with INCLUDE_ROUTES_BY_DEFAULT=True, to explicitly mark routes as not searchable.

    """
    view.__search_index__ = False
    return view


def searchable(view) -> callable:
    """
    Flask decorator to denote a view/route as "searchable", which will expose it to the API.

    To be used in conjunction with INCLUDE_ROUTES_BY_DEFAULT=False, to explicitly mark routes as searchable.
    """
    view.__search_index__ = True
    return view

def page_detail(title: str, description: str, teaser_image: str | None = None, weighting: int = 0, tags: list[str] = []) -> callable:
    """
    Flask decorator to attach a title, description, teaser image, weighting, and tags to a view/route, used in the API output.
    """

    def decorator(view) -> callable:
        view.__page_title__ = title
        view.__page_description__ = description
        view.__teaser_image__ = teaser_image
        view.__weighting__ = weighting
        view.__tags__ = tags
        return view

    return decorator