"""Utility transaction database loader compatible with the Two-Phase algorithm."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Set

from item_utility import ItemUtility
from transaction_tp import TransactionTP


class UtilityTransactionDatabaseTP:
    """Loads and stores transactions enriched with utility values."""

    def __init__(self) -> None:
        self.all_items: Set[int] = set()
        self.transactions: List[TransactionTP] = []

    def load_file(self, path: str | Path) -> None:
        input_path = Path(path)
        with input_path.open("r", encoding="utf-8") as reader:
            for line in reader:
                line = line.strip()
                if not line or line[0] in {"#", "%", "@"}:
                    continue
                self._process_transaction(line.split(":"))

    def _process_transaction(self, sections: List[str]) -> None:
        transaction_utility = int(sections[1])
        items = sections[0].strip().split()
        utilities = sections[2].strip().split()

        item_objects: List[ItemUtility] = []
        for item_str, util_str in zip(items, utilities):
            item = int(item_str)
            utility = int(util_str)
            item_objects.append(ItemUtility(item, utility))
            self.all_items.add(item)
        self.transactions.append(TransactionTP(item_objects, transaction_utility))

    def print_database(self) -> None:
        print("===================  Database ===================")
        for index, transaction in enumerate(self.transactions):
            print(f"0{index}:  {transaction}")

    def size(self) -> int:
        return len(self.transactions)

    def get_transactions(self) -> List[TransactionTP]:
        return self.transactions

    def get_all_items(self) -> Set[int]:
        return self.all_items

    def calculate_total_utility(self) -> float:
        return sum(tx.get_transaction_utility() for tx in self.transactions)
