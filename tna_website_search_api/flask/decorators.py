def searchable(view, title: str, description: str):
    """
    Flask decorator to denote a view/route as "searchable", which will expose it to the API.
    """
    view.__search_index__ = True