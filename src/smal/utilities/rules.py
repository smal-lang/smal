"""Module defining validation rules for state machines."""

from __future__ import annotations  # Until Python 3.14

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from smal.schemas.state import IllegalStateError, StateType
from smal.schemas.transition import IllegalTransitionError

if TYPE_CHECKING:
    from smal.schemas.state_machine import StateMachine


class RuleLike(Protocol):
    """Protocol defining the structure for an encapsulated validation rule for a SMAL state machine."""

    description: str
    enabled: bool
    group: str | None

    @property
    def name(self) -> str:
        """The name of this RuleLike."""

    def pre_evaluation(self, machine: StateMachine) -> None:
        """Handle any processing that needs to be done before evaluation of this rule.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        """

    def evaluate(self, machine: StateMachine) -> None:
        """Evaluate this rule against the given state machine.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        """

    def post_evaluation(self, machine: StateMachine) -> None:
        """Handle any post-processing that needs to be done after evaluation of this rule.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        """


@dataclass(frozen=True)
class Rule(RuleLike):
    """Base class for all RuleLike objects."""

    description: str = ""
    enabled: bool = True
    group: str | None = None

    @property
    def name(self) -> str:
        """Return the name of this Rule.

        Returns:
            str: The name of this rule.

        """
        parts = re.split(r"(?<=[a-z])(?=[A-Z])", self.__class__.__name__)
        return "-".join([p.lower() for p in parts])

    def pre_evaluation(self, machine: StateMachine) -> None:
        """Handle any processing that needs to be done before evaluation of this rule.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        """
        # NOTE: Not raising exception here, as this is an optional method

    def evaluate(self, machine: StateMachine) -> None:
        """Evaluate this rule against the given state machine.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        """
        raise NotImplementedError("Rule.evaluate is a required method and must be implemented by child classes of Rule.")

    def post_evaluation(self, machine: StateMachine) -> None:
        """Handle any post-processing that needs to be done after evaluation of this rule.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        """
        # NOTE: Not raising exception here, as this is an optional method


@dataclass(frozen=True)
class NoTransitionIntoRootState(Rule):
    """Rule enforcing that transitions into root states are illegal."""

    description: str = "Transitions cannot be made into a root state."

    def evaluate(self, machine: StateMachine) -> None:
        """Evalute this rule.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        Raises:
            IllegalTransitionError: If the state machine violates this rule.

        """
        root_state = machine.root_state
        # Not all valid state machines are required to have a root state, so if one doesn't exist, skip this rule
        if root_state is not None:
            incoming_transitions = machine.get_incoming_transitions(root_state)
            if incoming_transitions:
                raise IllegalTransitionError("Cannot transition into the root state.", incoming_transitions[0], machine.name)


@dataclass(frozen=True)
class NoTransitionOutOfFinalOrTerminal(Rule):
    """Rule enforcing that transitions out of the Final or Terminal pseudostates are illegal."""

    description: str = "Transitions cannot be made out of the Final or Terminal pseudostates."

    def evaluate(self, machine: StateMachine) -> None:
        """Evalute this rule.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        Raises:
            IllegalTransitionError: If the state machine violates this rule.

        """
        # Validate that all references exist
        for t in machine.transitions:
            src = machine.get_state(t.src)
            if src.type in {StateType.FINAL, StateType.TERMINAL}:
                raise IllegalTransitionError("Cannot transition out of a Final or Terminal pseudostate.", t, machine.name)


@dataclass(frozen=True)
class EntryExitStatesRequireParent(Rule):
    """Rule enforcing that Entry/Exit pseudostates are required to live within a Composite state."""

    description: str = "All Entry/Exit pseudostates are required to have a parent Composite state."

    def evaluate(self, machine: StateMachine) -> None:
        """Evalute this rule.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        Raises:
            IllegalStateError: If the state machine violates this rule.

        """
        flattened = machine.flatten(machine.states)
        for s in flattened.values():
            if s.type in {StateType.ENTRY, StateType.EXIT} and not s.is_substate:
                raise IllegalStateError("Entry / Exit pseudostates must be children of composite states.", s, machine.name)


@dataclass(frozen=True)
class DecisionsJunctionsRequireMultiOut(Rule):
    """Rule enforcing that Decision/Junction pseudostates are required to have >= 2 outgoing transitions."""

    description: str = "All Decision/Junction pseudostates are required to have >= 2 outgoing transitions."

    def evaluate(self, machine: StateMachine) -> None:
        """Evalute this rule.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        Raises:
            IllegalStateError: If the state machine violates this rule.

        """
        flattened = machine.flatten(machine.states)
        for s in flattened.values():
            if s.type in {StateType.DECISION, StateType.JUNCTION} and len(machine.get_outgoing_transitions(s)) < 2:
                raise IllegalStateError("Decision / Junction pseudostates must have >=2 outgoing transitions.", s, machine.name)


@dataclass(frozen=True)
class JoinsRequireMultiInSingleOut(Rule):
    """Rule enforcing that Join pseudostates are required to have >= 2 incoming transitions and exactly 1 outgoing transition."""

    description: str = "All Join pseudostates are required to have >= 2 incoming transitions and exactly 1 outgoing transition."

    def evaluate(self, machine: StateMachine) -> None:
        """Evalute this rule.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        Raises:
            IllegalStateError: If the state machine violates this rule.

        """
        flattened = machine.flatten(machine.states)
        for s in flattened.values():
            if s.type == StateType.JOIN:
                if len(machine.get_incoming_transitions(s)) < 2:
                    raise IllegalStateError("Join pseudostates must have >= 2 incoming transitions.", s, machine.name)
                if len(machine.get_outgoing_transitions(s)) != 1:
                    raise IllegalStateError("Join pseudostates must have exactly 1 outgoing transition.", s, machine.name)


@dataclass(frozen=True)
class ForksRequireSingleInMultiOut(Rule):
    """Rule enforcing that all Fork pseudostates are required to have exactly 1 incoming transition and >= 2 outgoing transitions."""

    description: str = "All Fork pseudostates are required to have exactly 1 incoming transition and >= 2 outgoing transitions."

    def evaluate(self, machine: StateMachine) -> None:
        """Evalute this rule.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        Raises:
            IllegalStateError: If the state machine violates this rule.

        """
        flattened = machine.flatten(machine.states)
        for s in flattened.values():
            if s.type == StateType.FORK:
                if len(machine.get_incoming_transitions(s)) != 1:
                    raise IllegalStateError("Fork pseudostates must have exactly 1 incoming transition.", s, machine.name)
                if len(machine.get_outgoing_transitions(s)) != 1:
                    raise IllegalStateError("Fork pseudostates must have >= 2 outgoing transitions.", s, machine.name)


@dataclass(frozen=True)
class AllStatesMustBeReachable(Rule):
    """Rule enforcing that all states (and substates) within the state machine must be reachable."""

    description: str = "All states (and substates) within the state machine must be reachable."

    def evaluate(self, machine: StateMachine) -> None:
        """Evalute this rule.

        Args:
            machine (StateMachine): The state machine being evaluated against.

        Raises:
            ValueError: If the state machine violates this rule.

        """
        root_state = machine.root_state
        if root_state is None:
            # Not all state machines have a root state, so if that's the case, fall back to its initial state as the root for reachability purposes
            root_state = machine.initial_state
        reachable_states = self._compute_reachable_states(root_state.name, machine.adjacency_list)
        all_states = set(machine.flatten(machine.states).keys())
        unreachable_states = all_states - reachable_states
        if unreachable_states:
            raise ValueError(f"Unreachable state(s) detected in state machine: {', '.join(unreachable_states)}")

    def _compute_reachable_states(self, root: str, adj: dict[str, list[str]]) -> set[str]:
        visited = set()
        stack = [root]
        while stack:
            s = stack.pop()
            if s in visited:
                continue
            visited.add(s)
            stack.extend(adj.get(s, []))
        return visited


ALL_RULES: list[RuleLike] = [
    NoTransitionIntoRootState(),
    NoTransitionOutOfFinalOrTerminal(),
    EntryExitStatesRequireParent(),
    DecisionsJunctionsRequireMultiOut(),
    JoinsRequireMultiInSingleOut(),
    ForksRequireSingleInMultiOut(),
    AllStatesMustBeReachable(),
]
