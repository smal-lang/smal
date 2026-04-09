"""Module defining helper functions for CLI commands to use."""

from __future__ import annotations  # Until Python 3.14

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from rich.console import Console
from rich.table import Table

from smal.utilities.persistence import SMALPersistence

console = Console()

_active_statuses: ContextVar[tuple[Any, ...]] = ContextVar("_active_statuses", default=())


@contextmanager
def prefer_inner_rich_statuses() -> Any:
    """Temporarily patch Rich so nested statuses pause their parents.

    This lets an inner ``Console.status(...)`` own the live area while it is active,
    which prevents flicker when imported code opens its own status spinner.

    Yields:
        Iterator[None]: A context in which nested status calls prefer the innermost status.

    """
    original_console_status = Console.status

    @contextmanager
    def prioritized_status(self: Console, *args: Any, **kwargs: Any) -> Any:
        active_statuses = _active_statuses.get()
        parent_status = active_statuses[-1] if active_statuses else None
        status = original_console_status(self, *args, **kwargs)
        token = _active_statuses.set((*active_statuses, status))

        if parent_status is not None:
            parent_status.stop()

        try:
            with status as current_status:
                yield current_status
        finally:
            _active_statuses.reset(token)
            if parent_status is not None:
                parent_status.start()

    Console.status = prioritized_status
    try:
        yield
    finally:
        Console.status = original_console_status


def echo_list(header: str, items: list[str], tab_size: int = 2, bold_header: bool = True) -> None:
    """Echo a rich list of items with pretty formatting.

    Args:
        header (str): The header to print above the list of items.
        items (list[str]): The list of items to print under the header.
        tab_size (int, optional): The number of spaces to use for indentation. Defaults to 2.
        bold_header (bool, optional): Whether to print the header in bold. Defaults to True.

    """
    if bold_header:
        console.print(f"[bold]{header.rstrip(': ')}:[/bold]")
    else:
        console.print(f"{header.rstrip(': ')}:")
    original_tab_size = console.tab_size
    console.tab_size = tab_size
    for item in items:
        console.print(f"\t• {item}")
    console.tab_size = original_tab_size


def echo_table(title: str, columns: list[str], rows: list[list[str]], col_metadata: dict[str, dict[str, Any]] | None = None) -> None:
    """Echo a rich table to stdout with the given title, columns and rows.

    Args:
        title (str): The title of the table.
        columns (list[str]): The column headers of the table.
        rows (list[list[str]]): The rows of the table, where each row is a list of cell values.
        col_metadata (dict[str, dict[str, Any]], optional): Optional metadata for columns, where keys are column names and values are dictionaries of keyword arguments to pass to Table.add_column(). Defaults to None.

    """
    table = Table(title=title)
    for col in columns:
        col_md = col_metadata.get(col, {}) if col_metadata else {}
        table.add_column(col, **col_md)
    for row in rows:
        table.add_row(*row)
    console.print(table)


def get_persistence() -> SMALPersistence:
    """Get the SMAL persistence file, which contains the enabled status of corrections.

    Returns:
        SMALPersistence: The SMAL persistence object.

    """
    try:
        return SMALPersistence.load()
    except FileNotFoundError:
        console.print("[yellow]No existing persistence data found. Creating new persistence with default settings.[/yellow]")
        persistence = SMALPersistence()
        persistence.save()
        return persistence
