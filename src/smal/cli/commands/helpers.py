"""Module defining helper functions for CLI commands to use."""

from __future__ import annotations  # Until Python 3.14

from rich.console import Console
from rich.table import Table

from smal.utilities.persistence import SMALPersistence

console = Console()


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


def echo_table(title: str, columns: list[str], rows: list[list[str]]) -> None:
    """Echo a rich table to stdout with the given title, columns and rows.

    Args:
        title (str): The title of the table.
        columns (list[str]): The column headers of the table.
        rows (list[list[str]]): The rows of the table, where each row is a list of cell values.

    """
    table = Table(title=title)
    for col in columns:
        table.add_column(col)
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
