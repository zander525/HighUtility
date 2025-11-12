"""Item and utility pairing used by the Two-Phase high-utility mining algorithm."""

from __future__ import annotations


class ItemUtility:
    """Represents an item together with its utility value in a transaction."""

    def __init__(self, item: int, utility: int) -> None:
        self.item = item
        self.utility = utility

    def __repr__(self) -> str:
        return f"[{self.item},{self.utility}]"
