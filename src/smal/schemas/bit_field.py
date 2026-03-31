from __future__ import annotations  # Until Python 3.14

from typing import ClassVar

from pydantic import BaseModel, Field, field_validator

from smal.schemas.utilities import IdentifierValidationMixin


class BitField(IdentifierValidationMixin, BaseModel):
    """Schema defining an individual field within a bitfield. Not to be confused with the bitfield itself."""

    IDENTIFIER_FIELDS: ClassVar[tuple[str]] = ("name",)

    name: str = Field(..., description="The name of the bit field (not to be confused with bitfield).")
    bit: int = Field(..., description="The bit index within the bitfield this field is assigned to.")

    @field_validator("bit")
    def validate_bit(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Bit index must be >= 0")
        return v
