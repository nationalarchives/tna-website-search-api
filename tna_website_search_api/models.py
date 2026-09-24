from pydantic import BaseModel, HttpUrl
from datetime import datetime


class ApplicationPage(BaseModel):
    """
    Pydantic model to validate a ApplicationPage output.

    ApplicationPages are the distinct URLs of an application, e.g. "www.example.com/about". They are children of Applications.
    """
    title: str
    url: str # e.g. "/about"
    description: str
    teaser_image: HttpUrl | None = None


class Application(BaseModel):
    """
    Pydantic model to validate an Application output.

    Applications are the root of the application, e.g. "www.example.com". They contain the shared metadata of
    all ApplicationPages.
    """
    title: str
    version: str
    description: str
    base_url: HttpUrl
    type_label: str | None = None
    first_published_at: datetime | None = None
    last_published_at: datetime | None = None
    pages: list[ApplicationPage] = []