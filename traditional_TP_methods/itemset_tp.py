"""High-utility itemset representation for the Two-Phase algorithm."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Set


@dataclass
class ItemsetTP:
    """Represents an ordered itemset together with its utility metadata."""

    items: List[int] = field(default_factory=list)
    utility: int = 0
    transactions_ids: Optional[Set[int]] = None

    def add_item(self, value: int) -> None:
        self.items.append(value)

    def get_items(self) -> List[int]:
        return self.items

    def get(self, index: int) -> int:
        return self.items[index]

    def set_tidset(self, tids: Iterable[int]) -> None:
        self.transactions_ids = set(tids)

    def get_tidset(self) -> Set[int]:
        return self.transactions_ids or set()

    def size(self) -> int:
        return len(self.items)

    def get_absolute_support(self) -> int:
        return len(self.transactions_ids) if self.transactions_ids else 0

    def get_relative_support(self, nb_object: int) -> float:
        if not self.transactions_ids or nb_object == 0:
            return 0.0
        return len(self.transactions_ids) / nb_object

    def get_relative_support_as_string(self, nb_object: int) -> str:
        return f"{self.get_relative_support(nb_object):.4f}".rstrip("0").rstrip(".")

    def increment_utility(self, increment: int) -> None:
        self.utility += increment

    def get_utility(self) -> int:
        return self.utility

    def __str__(self) -> str:
        return " ".join(str(item) for item in self.items) + (" " if self.items else "")
