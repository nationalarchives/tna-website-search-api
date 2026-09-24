from django.apps import AppConfig


class WebsiteSearchAPIConfig(AppConfig):
    name = "tna_website_search_api.django"
    label = "tna_website_search_api"
    verbose_name = "The National Archives Website Search API"

    def ready(self) -> None:
        from . import checks
