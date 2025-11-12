"""Python port of the Two-Phase high-utility itemset mining algorithm."""

from __future__ import annotations

import time
from typing import Dict, Iterable, List, Optional, Set

from itemset_tp import ItemsetTP
from itemsets_tp import ItemsetsTP
from item_utility import ItemUtility
from memory_logger import get_instance as get_memory_logger
from transaction_tp import TransactionTP
from utility_transaction_database_tp import UtilityTransactionDatabaseTP


class AlgoTwoPhase:
    """Implementation of the Two-Phase algorithm using Python data structures."""

    def __init__(self) -> None:
        self.high_utility_itemsets: Optional[ItemsetsTP] = None
        self.database: Optional[UtilityTransactionDatabaseTP] = None
        self.min_utility: int = 0
        self.start_timestamp: float = 0.0
        self.end_timestamp: float = 0.0
        self.candidates_count: int = 0

    def run_algorithm(
        self, database: UtilityTransactionDatabaseTP, min_utility: int
    ) -> ItemsetsTP:
        self.database = database
        self.min_utility = min_utility

        memory_logger = get_memory_logger()
        memory_logger.reset()
        self.start_timestamp = time.time()

        self.high_utility_itemsets = ItemsetsTP("HIGH UTILITY ITEMSETS")
        self.candidates_count = 0

        candidates_size_1 = self._generate_size_one_candidates()
        current_level = candidates_size_1

        while True:
            previous_count = self.high_utility_itemsets.get_itemsets_count()
            current_level = self.generate_candidate_size_k(
                current_level, self.high_utility_itemsets
            )
            if previous_count == self.high_utility_itemsets.get_itemsets_count():
                break

        memory_logger.check_memory()
        self.candidates_count = self.high_utility_itemsets.get_itemsets_count()
        self._evaluate_candidates()
        memory_logger.check_memory()

        self.end_timestamp = time.time()
        return self.high_utility_itemsets

    def _generate_size_one_candidates(self) -> List[ItemsetTP]:
        assert self.database is not None
        map_item_tidsets: Dict[int, Set[int]] = {}
        map_item_twu: Dict[int, int] = {}
        max_item = -1

        for tid, transaction in enumerate(self.database.get_transactions()):
            for item_utility in transaction.get_items():
                item = item_utility.item
                max_item = max(max_item, item)
                tidset = map_item_tidsets.setdefault(item, set())
                tidset.add(tid)
                twu = map_item_twu.get(item, 0)
                map_item_twu[item] = twu + transaction.get_transaction_utility()

        candidates: List[ItemsetTP] = []
        for item in range(max_item + 1):
            estimated_utility = map_item_twu.get(item)
            if estimated_utility is None or estimated_utility < self.min_utility:
                continue
            itemset = ItemsetTP()
            itemset.add_item(item)
            itemset.set_tidset(map_item_tidsets[item])
            candidates.append(itemset)
            assert self.high_utility_itemsets is not None
            self.high_utility_itemsets.add_itemset(itemset, itemset.size())
        return candidates

    def _evaluate_candidates(self) -> None:
        assert self.high_utility_itemsets is not None
        assert self.database is not None
        for level in self.high_utility_itemsets.get_levels():
            index = 0
            while index < len(level):
                candidate = level[index]
                self._evaluate_single_candidate(candidate)
                if candidate.get_utility() < self.min_utility:
                    level.pop(index)
                    self.high_utility_itemsets.decrease_count()
                else:
                    index += 1

    def _evaluate_single_candidate(self, candidate: ItemsetTP) -> None:
        assert self.database is not None
        candidate_items = set(candidate.get_items())
        candidate.utility = 0
        for transaction in self.database.get_transactions():
            matches = [
                iu for iu in transaction.get_items() if iu.item in candidate_items
            ]
            if len(matches) == candidate.size():
                utility_increment = sum(iu.utility for iu in matches)
                candidate.increment_utility(utility_increment)

    def generate_candidate_size_k(
        self, level_k_minus_1: Iterable[ItemsetTP], candidates_htwui: ItemsetsTP
    ) -> List[ItemsetTP]:
        assert self.database is not None

        new_candidates: List[ItemsetTP] = []
        level_list = list(level_k_minus_1)
        for index1, itemset1 in enumerate(level_list):
            for itemset2 in level_list[index1 + 1 :]:
                if not self._can_join(itemset1, itemset2):
                    continue
                candidate = self._join_itemsets(itemset1, itemset2)
                tidset = itemset1.get_tidset() & itemset2.get_tidset()
                candidate.set_tidset(tidset)
                twu = sum(
                    self.database.get_transactions()[tid].get_transaction_utility()
                    for tid in tidset
                )
                if twu >= self.min_utility:
                    candidates_htwui.add_itemset(candidate, candidate.size())
                    new_candidates.append(candidate)
                    print(f"candidate : {candidate},TWU : {twu}")
        return new_candidates

    @staticmethod
    def _can_join(itemset1: ItemsetTP, itemset2: ItemsetTP) -> bool:
        prefix1 = itemset1.get_items()[:-1]
        prefix2 = itemset2.get_items()[:-1]
        if prefix1 != prefix2:
            return False
        return itemset1.get_items()[-1] < itemset2.get_items()[-1]

    @staticmethod
    def _join_itemsets(itemset1: ItemsetTP, itemset2: ItemsetTP) -> ItemsetTP:
        new_items = list(itemset1.get_items())
        new_items.append(itemset2.get_items()[-1])
        return ItemsetTP(items=new_items)

    def print_stats(self) -> None:
        elapsed_ms = (self.end_timestamp - self.start_timestamp) * 1000
        assert self.database is not None
        assert self.high_utility_itemsets is not None
        print("=============  TWO-PHASE ALGORITHM - STATS =============")
        print(f" Transactions count from database : {self.database.size()}")
        print(f" Candidates count : {self.candidates_count}")
        print(
            " High-utility itemsets count : "
            f"{self.high_utility_itemsets.get_itemsets_count()}"
        )
        print(f" Total time ~ {elapsed_ms:.0f} ms")
        print("===================================================")
