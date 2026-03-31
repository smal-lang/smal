from __future__ import annotations  # Until Python 3.14

from pydantic import BaseModel, Field


class Transition(BaseModel):
    """Schema defining a transition between states in a state machine."""

    src_state: str = Field(..., description="The name of the state the machine must be in in order for evt to trigger this transition.")
    evt: str = Field(..., description="The name of the event that triggers this transition.")
    actions: list[str] = Field(..., description="The sequence of functions to invoke when evt is received while in src_state.")
    tgt_state: str = Field(..., description="The state to transition into after executing actions in response to receiving evt while in src_state.")
    tgt_entry_evt: str | None = Field(default=None, description="Event to trigger upon entering tgt_state, if any.")

    def __repr__(self) -> str:
        return f"({self.src_state}, {self.evt}, [{', '.join(self.actions)}], {self.tgt_state}, {self.tgt_entry_evt})"
