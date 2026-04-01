from __future__ import annotations  # Until Python 3.14

from typing import ClassVar

from pydantic import BaseModel, Field, field_validator

from smal.schemas.utilities import IdentifierValidationMixin


class Enumeration(IdentifierValidationMixin, BaseModel):
    """Schema defining an enumeration."""

    IDENTIFIER_FIELDS: ClassVar[tuple[str]] = ("name",)

    name: str = Field(..., description="The name of the enumeration.")
    values: dict[int, str] = Field(..., description="The mapping of enumeration values to the labels.")

    @field_validator("values")
    def validate_values(cls, v: dict[int, str]) -> dict[int, str]:
        for key, val in v.items():
            if key < 0:
                raise ValueError("Enum keys must be non-negative")
            if not val.isidentifier():
                raise ValueError("Invalid enum value name: {val}")
        return v
