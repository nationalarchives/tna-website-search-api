class WebsiteSearchAPIConfig:
    INCLUDE_ROUTES_BY_DEFAULT: bool = True # If True, all routes are included by default. You must explicitly mark routes as not searchable to exclude them. If False, then you must explicitly mark routes as searchable to include them.
    WEBSITE_SEARCH_API_ENABLED: bool = True # Enable/Disable API
    WEBSITE_SEARCH_API_PREFIX: str = "/api" # Prefix for the API endpoint
    WEBSITE_SEARCH_APPLICATION_METADATA: dict = {
        "title": "Application title",
        "version": "1.0.0",
        "description": "Application description",
        "base_url": "https://www.example.com/some-application-name",
        "type_label": None,
        "first_published_at": None,
        "last_published_at": None,
    } # Config for the Application model
