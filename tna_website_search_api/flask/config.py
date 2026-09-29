import os
from tna_utilities import strtobool

class WebsiteSearchAPIConfig:
    # TODO: Better way of managing config...
    INCLUDE_ROUTES_BY_DEFAULT: bool = strtobool(os.getenv("INCLUDE_ROUTES_BY_DEFAULT", "True")) # If True, all routes are included by default. You must explicitly mark routes as not searchable to exclude them. If False, then you must explicitly mark routes as searchable to include them.
    WEBSITE_SEARCH_API_ENABLED: bool = strtobool(os.getenv("WEBSITE_SEARCH_API_ENABLED", "True")) # Enable/Disable API
    WEBSITE_SEARCH_API_PREFIX: str = os.getenv("WEBSITE_SEARCH_API_PREFIX", "/api") # Prefix for the API endpoint
