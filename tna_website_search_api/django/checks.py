from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.checks import Error, Tags, register
from django.utils.module_loading import import_string


@register(Tags.urls)
def check_configuration(**kwargs: Any) -> list[Error]:
    del kwargs
    errors: list[Error] = []
    configuration = getattr(settings, "TNA_WEBSITE_SEARCH_API", {})
    providers = configuration.get("PROVIDERS", ())
    if not isinstance(providers, list | tuple):
        return [
            Error(
                "TNA_WEBSITE_SEARCH_API['PROVIDERS'] must be a list or tuple.",
                id="tna_website_search_api.E001",
            )
        ]
    for provider_path in providers:
        try:
            provider = import_string(provider_path)
        except (ImportError, AttributeError) as error:
            errors.append(
                Error(
                    f"Unable to import page provider {provider_path!r}: {error}",
                    id="tna_website_search_api.E002",
                )
            )
            continue
        if not callable(provider):
            errors.append(
                Error(
                    f"Page provider {provider_path!r} is not callable.",
                    id="tna_website_search_api.E003",
                )
            )
    return errors