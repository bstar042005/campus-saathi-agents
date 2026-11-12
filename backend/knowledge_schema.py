from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class KnowledgeBase(BaseModel):
    """Fields shared by every knowledge record."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: str
    aliases: list[str] = Field(default_factory=list)
    node_id: Optional[str] = None
    source: str = Field(min_length=1)
    last_verified: date

    @field_validator("id", "source")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field cannot be blank")
        return value.strip()

    @field_validator("aliases")
    @classmethod
    def clean_aliases(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("Aliases cannot contain blank values")
        return [value.strip() for value in values]

    @field_validator("last_verified")
    @classmethod
    def date_cannot_be_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("last_verified cannot be a future date")
        return value


class Contact(KnowledgeBase):
    type: Literal["contact"]

    name: str = Field(min_length=1)
    office: str = Field(min_length=1)
    phone: Optional[str] = None
    email: Optional[str] = None
    location_text: str = Field(min_length=1)
    hours: Optional[str] = None


class Club(KnowledgeBase):
    type: Literal["club"]

    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    description: str = Field(min_length=1)
    how_to_join: str = Field(min_length=1)
    contact_id: Optional[str] = None


class FaqEntry(KnowledgeBase):
    type: Literal["faq"]

    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    required_documents: list[str] = Field(default_factory=list)
    category: str = Field(min_length=1)
    related_step: Optional[str] = None


class OfficialLink(KnowledgeBase):
    type: Literal["official_link"]

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    url: str = Field(min_length=1)
    description: str = Field(min_length=1)

    @field_validator("url")
    @classmethod
    def must_use_https(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith("https://"):
            raise ValueError("URL must start with https://")
        return value