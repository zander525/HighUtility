"""Utility-annotated transaction representation."""

from __future__ import annotations

from typing import Iterable, List

from item_utility import ItemUtility


class TransactionTP:
    """Represents a transaction containing items with per-item utilities."""

    def __init__(self, items_utilities: Iterable[ItemUtility], transaction_utility: int) -> None:
        self.items_utilities: List[ItemUtility] = list(items_utilities)
        self.transaction_utility = transaction_utility

    def get_items(self) -> List[ItemUtility]:
        return self.items_utilities

    def get(self, index: int) -> ItemUtility:
        return self.items_utilities[index]

    def print(self) -> None:
        print(self.__str__(), end="")

    def __str__(self) -> str:
        items_str = " ".join(repr(item) for item in self.items_utilities)
        return f"{items_str} :{self.transaction_utility}: {items_str} "

    def contains(self, item: int) -> bool:
        for element in self.items_utilities:
            if element.item == item:
                return True
            if element.item > item:
                return False
        return False

    def size(self) -> int:
        return len(self.items_utilities)

    def get_items_utilities(self) -> List[ItemUtility]:
        return self.items_utilities

    def get_transaction_utility(self) -> int:
        return self.transaction_utility
