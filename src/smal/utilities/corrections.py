"""Module defining validation rules for state machines."""

from __future__ import annotations  # Until Python 3.14

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from smal.schemas.state import StateType

if TYPE_CHECKING:
    from smal.schemas.state_machine import StateMachine


class CorrectionLike(Protocol):
    """Protocol defining the structure for an encapsulated correction for a SMAL state machine."""

    description: str
    group: str | None

    @property
    def name(self) -> str:
        """The name of this CorrectionLike."""

    def pre_application(self, machine: StateMachine) -> None:
        """Handle any processing that needs to be done before applying this correction.

        Args:
            machine (StateMachine): The state machine the correction is being applied to.

        """

    def apply(self, machine: StateMachine) -> None:
        """Apply this correction to the given state machine.

        Args:
            machine (StateMachine): The state machine the correction is being applied to.

        """

    def post_application(self, machine: StateMachine) -> None:
        """Handle any post-processing that needs to be done after applying this correction.

        Args:
            machine (StateMachine): The state machine the correction is being applied to.

        """


@dataclass
class Correction(CorrectionLike):
    """Base class for all CorrectionLike objects."""

    description: str = ""
    group: str | None = None

    @property
    def name(self) -> str:
        """Return the name of this Correction.

        Returns:
            str: The name of this correction.

        """
        parts = re.split(r"(?<=[a-z])(?=[A-Z])", self.__class__.__name__)
        return "-".join([p.lower() for p in parts])

    def pre_application(self, machine: StateMachine) -> None:
        """Handle any processing that needs to be done before applying this correction.

        Args:
            machine (StateMachine): The state machine the correction is being applied to.

        """
        # NOTE: Not raising exception here, as this is an optional method

    def apply(self, machine: StateMachine) -> None:
        """Apply this correction to the given state machine.

        Args:
            machine (StateMachine): The state machine the correction is being applied to.

        """
        raise NotImplementedError("Correction.apply is a required method and must be implemented by child classes of Correction.")

    def post_application(self, machine: StateMachine) -> None:
        """Handle any post-processing that needs to be done after applying this correction.

        Args:
            machine (StateMachine): The state machine the correction is being applied to.

        """
        # NOTE: Not raising exception here, as this is an optional method


@dataclass
class HideCompositeToInitialSubstateTransitions(Correction):
    """Correction that detects transitions from the root of a composite state to its initial substate and hides them from diagramming."""

    description: str = "Detects transitions from the root of a composite state to its initial substate and hides them from diagramming."

    def apply(self, machine: StateMachine) -> None:
        """Apply this correction.

        Args:
            machine (StateMachine): The state machine the correction is being applied to.

        """
        for t in machine.transitions:
            src = machine.get_state(t.src)
            if not src.is_composite:
                continue
            tgt = machine.get_state(t.tgt)
            if tgt.parent_name != src.name and tgt.type == StateType.INITIAL:
                continue
            logging.debug("CORRECTION: Hiding a composite root to initial substate transition from diagramming...")
            t.set_graphable(False)


@dataclass
class HideCompositeToRootSimpleStateTransitions(Correction):
    """Correction that detects transitions from the root of a composite state to root-level simple states and hides them from diagramming."""

    description: str = "Detects transitions from the root of a composite state to root-level simple states and hides them from diagramming."

    def apply(self, machine: StateMachine) -> None:
        """Apply this correction.

        Args:
            machine (StateMachine): The state machine the correction is being applied to.

        """
        for t in machine.transitions:
            src = machine.get_state(t.src)
            if not src.is_composite:
                continue
            tgt = machine.get_state(t.tgt)
            if tgt.is_substate:
                continue
            logging.debug("CORRECTION: Hiding a composite root to root-level simple state transition from diagramming...")
            t.set_graphable(False)


ALL_CORRECTIONS: list[CorrectionLike] = [
    HideCompositeToInitialSubstateTransitions(),
    HideCompositeToRootSimpleStateTransitions(),
]
