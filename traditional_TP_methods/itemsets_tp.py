"""Container for storing high-utility itemsets grouped by size."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from itemset_tp import ItemsetTP


class ItemsetsTP:
    """Stores discovered itemsets by level (size)."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.levels: List[List[ItemsetTP]] = [[]]
        self.itemsets_count = 0

    def print_itemsets(self, transaction_count: int) -> None:
        print(f" ------- {self.name} -------")
        pattern_count = 0
        for level_id, level in enumerate(self.levels):
            print(f"  L{level_id} ")
            for itemset in level:
                support = itemset.get_absolute_support()
                print(
                    f"  pattern {pattern_count}  {itemset}"
                    f"#SUP: {support} #UTIL: {itemset.get_utility()}"
                )
                pattern_count += 1
        print(" --------------------------------")

    def save_results_to_file(self, output: str | Path, transaction_count: int) -> None:
        path = Path(output)
        with path.open("w", encoding="utf-8") as writer:
            for level in self.levels:
                for itemset in level:
                    support = itemset.get_relative_support_as_string(transaction_count)
                    writer.write(
                        f"{itemset}#SUP: {support} #UTIL: {itemset.get_utility()}\n"
                    )

    def add_itemset(self, itemset: ItemsetTP, k: int) -> None:
        while len(self.levels) <= k:
            self.levels.append([])
        self.levels[k].append(itemset)
        self.itemsets_count += 1

    def get_levels(self) -> List[List[ItemsetTP]]:
        return self.levels

    def get_itemsets_count(self) -> int:
        return self.itemsets_count

    def decrease_count(self) -> None:
        if self.itemsets_count:
            self.itemsets_count -= 1
