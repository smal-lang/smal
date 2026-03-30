from __future__ import annotations  # Until Python 3.14

from enum import Enum
from functools import cached_property
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self

from smal.schemas.utilities import IdentifierValidationMixin


class SMALStateType(str, Enum):
    NORMAL = "normal"
    INITIAL = "initial"
    FINAL = "final"
    COMPOSITE = "composite"
    DECISION = "decision"
    ERROR = "error"

    @cached_property
    def is_pseudostate(self) -> bool:
        return self in {SMALStateType.INITIAL, SMALStateType.FINAL, SMALStateType.DECISION, SMALStateType.ERROR}

    @cached_property
    def graphviz_shape(self) -> str:
        return {
            self.NORMAL: "ellipse",
            self.INITIAL: "circle",
            self.FINAL: "doublecircle",
            self.COMPOSITE: "box",
            self.DECISION: "diamond",
            self.ERROR: "octagon",
        }[self]


class SMALState(IdentifierValidationMixin, BaseModel):
    IDENTIFIER_FIELDS: ClassVar[tuple[str]] = ("name",)

    name: str = Field(..., description="A unique name for the state, which serves as its identifier and may be used in transitions.")
    substates: list[SMALState] = Field(default_factory=list, description="Substates of the state, if any.")
    id: int | None = Field(
        default=None,
        description="A unique integer identifier for the state. If not provided, it may be auto-assigned based on the order of definition or other criteria.",
    )
    description: str | None = Field(default=None, description="A human-readable description of the state.")
    type: SMALStateType = Field(default=SMALStateType.NORMAL, description="The type of the state, which may affect its behavior and/or visualization.")

    @field_validator("substates", mode="before")
    def expand_short_form_substates(cls, v: list[dict | str] | None) -> list[SMALState]:
        if v is None:
            return []
        expanded_substates = []
        for item in v:
            if isinstance(item, str):
                expanded_substates.append(SMALState(name=item))
            elif isinstance(item, dict):
                expanded_substates.append(SMALState.model_validate(item))
            else:
                raise ValueError(f"Invalid state definition: {item}. Must be either a string or a dictionary.")
        return expanded_substates

    @model_validator(mode="after")
    def validate_state_type(self) -> Self:
        # Always coerce type to composite (superstate) if this state has substates
        if self.substates:
            if self.type.is_pseudostate:
                raise ValueError(f"SMALState<{self.name}>: Pseudostate '{self.type.value}' cannot have substates.")
            self.type = SMALStateType.COMPOSITE
        # Validate substate name uniqueness
        substate_names = [s.name for s in self.substates]
        if len(substate_names) != len(set(substate_names)):
            raise ValueError(f"Failed to validate SMALState '{self.name}'. All substate names must be unique.")
        # Validate no containment cycles
        self._validate_no_cycles(parent_chain=[])
        return self

    def _validate_no_cycles(self, parent_chain: list[str]) -> None:
        if self.name in parent_chain:
            raise ValueError(f"SMALState<{self.name}>: Containment cycle detected - {' → '.join(parent_chain + [self.name])}")
        for ss in self.substates:
            ss._validate_no_cycles(parent_chain + [self.name])

    @property
    def is_composite(self) -> bool:
        return self.type == SMALStateType.COMPOSITE
