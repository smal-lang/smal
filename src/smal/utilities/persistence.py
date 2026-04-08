"""Module defining utilities for persistence of data."""

from __future__ import annotations  # Until Python 3.14

import logging
import shutil
from pathlib import Path
from typing import ClassVar

from platformdirs import user_data_dir
from pydantic import BaseModel, Field

from smal.utilities.corrections import ALL_CORRECTIONS, Correction
from smal.utilities.rules import ALL_RULES, Rule


class SMALPersistence(BaseModel):
    """Model representing the persistence of SMAL data, including rules and corrections."""

    DEFAULT_PATH: ClassVar[Path] = Path(user_data_dir(appname="smal", appauthor=False)) / "persistence.json"

    rules: dict[str, bool] = Field(
        default_factory=lambda: dict.fromkeys([r.name for r in ALL_RULES], True),
        description="A dictionary mapping rule names to their enabled/disabled status.",
    )
    corrections: dict[str, bool] = Field(
        default_factory=lambda: dict.fromkeys([c.name for c in ALL_CORRECTIONS], False),
        description="A dictionary mapping correction names to their enabled/disabled status.",
    )

    @staticmethod
    def clean() -> None:
        """Clean the persistence data by deleting the persistence file and its application directory."""
        app_dir = SMALPersistence.DEFAULT_PATH.parent
        if app_dir.exists():
            shutil.rmtree(app_dir)
            logging.debug("Persistence data cleaned by removing directory %s", app_dir)

    @classmethod
    def load(cls, path: Path | str = DEFAULT_PATH) -> SMALPersistence:
        """Load the persistence data from a JSON file.

        Args:
            path (Path | str): The path to the JSON file from which to load the data. Defaults to DEFAULT_PATH.

        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Persistence file not found at {path}. Please save the persistence data first.")
        with path.open("r", encoding="utf-8") as f:
            return cls.model_validate_json(f.read())

    def enable_correction(self, correction: str | Correction, enabled: bool, write_to_file: bool = True) -> None:
        """Enable or disable a specific correction.

        Args:
            correction (str | Correction): The name of the correction to enable or disable, or a Correction object.
            enabled (bool): Whether to enable (True) or disable (False) the correction.
            write_to_file (bool): Whether to save the updated persistence data to file after changing the correction status. Defaults to True.

        """
        correction_name = correction if isinstance(correction, str) else correction.name
        if correction_name not in self.corrections:
            raise ValueError(f"Correction '{correction_name}' is not recognized.")
        self.corrections[correction_name] = enabled
        logging.debug("Correction '%s' set to %s.", correction_name, enabled)
        if write_to_file:
            self.save()

    def enable_rule(self, rule: str | Rule, enabled: bool, write_to_file: bool = True) -> None:
        """Enable or disable a specific rule.

        Args:
            rule (str | Rule): The name of the rule to enable or disable, or a Rule object.
            enabled (bool): Whether to enable (True) or disable (False) the rule.
            write_to_file (bool): Whether to save the updated persistence data to file after changing the rule status. Defaults to True.

        """
        rule_name = rule if isinstance(rule, str) else rule.name
        if rule_name not in self.rules:
            raise ValueError(f"Rule '{rule_name}' is not recognized.")
        self.rules[rule_name] = enabled
        logging.debug("Rule '%s' set to %s.", rule_name, enabled)
        if write_to_file:
            self.save()

    def is_correction_enabled(self, correction: str | Correction) -> bool:
        """Check if a specific correction is enabled.

        Args:
            correction (str | Correction): The name of the correction to check, or a Correction object.

        Returns:
            bool: True if the correction is enabled, False otherwise.

        """
        correction_name = correction if isinstance(correction, str) else correction.name
        if correction_name not in self.corrections:
            raise ValueError(f"Correction '{correction_name}' is not recognized.")
        return self.corrections[correction_name]

    def is_rule_enabled(self, rule: str | Rule) -> bool:
        """Check if a specific rule is enabled.

        Args:
            rule (str | Rule): The name of the rule to check, or a Rule object.

        Returns:
            bool: True if the rule is enabled, False otherwise.

        """
        rule_name = rule if isinstance(rule, str) else rule.name
        if rule_name not in self.rules:
            raise ValueError(f"Rule '{rule_name}' is not recognized.")
        return self.rules[rule_name]

    def save(self, path: Path | str = DEFAULT_PATH) -> None:
        """Save the persistence data to a JSON file.

        Args:
            path (Path | str): The path to the JSON file where the data will be saved. Defaults to DEFAULT_PATH.

        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=4))
        logging.debug("Persistence data saved to %s", path)
