
"""
THUI-Mine (Temporal High Utility Itemsets) — Python reference implementation

Implements the core ideas from THUI-Mine:
- Fig. 3: Pre-processing procedure (initial mining over an initial window)
- Fig. 4: Incremental procedure (slide the window: delete old partitions, add new ones)

This module favors clarity and debuggability over micro-optimizations.
It is suitable for datasets of modest size when prototyping the algorithm.

Key terms (matching the paper's notation):
- Transaction: dict[item -> quantity], e.g., {"A": 2, "B": 1}
- Utility table: dict[item -> external utility s(i)]
- Utility of an item in a transaction: u(i, T) = o(i, T) * s(i)
- Transaction utility: tu(T) = sum_{i in T} u(i, T)
- Transaction-Weighted Utilization (TWU) of an itemset X across a set of transactions:
  twu(X) = sum_{T: X subset of T} tu(T)
- Filtering threshold per partition: s_part = e / num_partitions
  (Cumulative threshold for a candidate that started at partition p and is evaluated at partition i:
   threshold = (i - p + 1) * s_part)

Usage overview:
1) Build partitions: a list of partitions; each partition is a list of transactions (dicts).
2) Call THUIMine(...).preprocess(partitions) to mine the initial window (Fig. 3).
3) Call .incremental(delete_k, added_partitions) to slide the window (Fig. 4).

Author: ChatGPT (Python port for educational use)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Iterable, Tuple, Set, FrozenSet, Optional
from collections import defaultdict
import itertools


# -----------------------------
# Data classes
# -----------------------------

@dataclass
class CFEntry:
    """Cumulative Filter entry for an itemset.
    We keep per-partition TWU contributions to enable precise deletion (Fig. 4 first sub-step).
    """
    start: int                               # 1-based index of the partition where the itemset was added to CF
    twu_total: float = 0.0                   # Sum of TWU over current window (consistent with twu_per_partition)
    twu_per_partition: Dict[int, float] = field(default_factory=dict)  # partition_idx -> twu contribution

    def refresh_totals(self) -> None:
        self.twu_total = sum(self.twu_per_partition.values())

    def cumulative_threshold(self, s_part: float, current_partition_idx: int) -> float:
        """(i - start + 1) * s_part"""
        window_len = current_partition_idx - self.start + 1
        return max(0.0, window_len * s_part)


@dataclass
class MiningResult:
    """Container for outputs and state to support further incremental updates."""
    thut_itemsets: Dict[FrozenSet[str], float]         # Final temporal high utility itemsets with exact utility
    cf: Dict[FrozenSet[str], CFEntry]                  # Cumulative filter for 2-itemsets and (optionally) 1-itemsets
    twu1_high: Set[str]                                # High TWU 1-item items from preprocessing (for candidate gen)
    # bookkeeping
    num_partitions: int
    s_global: float
    s_part: float
    utilities: Dict[str, float]                        # s(i) external utility
    # Save a shallow copy of the partitions list that are currently in-window (for the next incremental step)
    # Each partition is a list of transactions; each transaction is dict[item -> qty]
    window_partitions: List[List[Dict[str, float]]]


# -----------------------------
# Helper functions
# -----------------------------

def transaction_utility(tx: Dict[str, float], utilities: Dict[str, float]) -> float:
    return sum(qty * utilities.get(item, 0.0) for item, qty in tx.items())


def items_in_tx(tx: Dict[str, float]) -> Set[str]:
    return {i for i, q in tx.items() if q != 0}


def power_join_pairs(items: Iterable[str]) -> Iterable[FrozenSet[str]]:
    """Generate all 2-itemset combinations as frozensets."""
    return (frozenset(pair) for pair in itertools.combinations(sorted(items), 2))


def contains_itemset(tx_items: Set[str], itemset: FrozenSet[str]) -> bool:
    return itemset.issubset(tx_items)


def candidate_join_from_twu2i(twu2i: Set[FrozenSet[str]], k: int) -> Set[FrozenSet[str]]:
    """Join step using TWU-2-itemsets to propose larger candidates (k>=3).
    Heuristic: any k-itemset candidate must have all its 2-subsets present in TWU2I.
    """
    if k < 3:
        raise ValueError("k must be >= 3 for candidate_join_from_twu2i.")
    items = sorted({x for pair in twu2i for x in pair})
    candidates: Set[FrozenSet[str]] = set()
    for comb in itertools.combinations(items, k):
        fs = frozenset(comb)
        # prune if any 2-subset is not in twu2i
        all_2_subsets_ok = all(frozenset(p) in twu2i for p in itertools.combinations(fs, 2))
        if all_2_subsets_ok:
            candidates.add(fs)
    return candidates


# -----------------------------
# Core class
# -----------------------------

class THUIMine:
    def __init__(self, utilities: Dict[str, float], min_utility_global: float):
        """
        :param utilities: external utility table s(i) for each item
        :param min_utility_global: global threshold e (e.g., 120 in the example)
        """
        self.utilities = dict(utilities)
        self.e = float(min_utility_global)

    # -------- Fig. 3: Pre-processing --------

    def preprocess(self, partitions: List[List[Dict[str, float]]]) -> MiningResult:
        """Run the initial mining over db1,n (Fig. 3).
        :param partitions: list of partitions; partition = list of transactions (dict item->qty)
        :return: MiningResult containing THUI, CF, and state for future incremental updates
        """
        if not partitions:
            return MiningResult({}, {}, set(), 0, self.e, 0.0, self.utilities, [])

        n = len(partitions)
        s_part = self.e / n

        cf: Dict[FrozenSet[str], CFEntry] = {}
        twu1_high: Set[str] = set()  # high TWU 1-items across the whole initial window (progressively selected)

        # Progressive processing over partitions (cumulative filter CF for 2-itemsets)
        for p_idx, part in enumerate(partitions, start=1):
            # Compute transaction utilities and 1-item TWU for this partition
            tu_list: List[Tuple[Set[str], float]] = []
            twu1_this_part: Dict[str, float] = defaultdict(float)
            for tx in part:
                tx_items = items_in_tx(tx)
                if not tx_items:
                    continue
                tu = transaction_utility(tx, self.utilities)
                tu_list.append((tx_items, tu))
                for i in tx_items:
                    twu1_this_part[i] += tu

            # Identify high TWU 1-items in this partition (>= s_part)
            high1 = {i for i, val in twu1_this_part.items() if val >= s_part}
            # Add to global progressive set (carry-over)
            twu1_high |= high1

            # Generate 2-item candidates from high1 in THIS partition (new joins)
            for pair in power_join_pairs(high1):
                entry = cf.get(pair)
                if entry is None:
                    entry = CFEntry(start=p_idx)
                    cf[pair] = entry
                # Accumulate TWU contribution from this partition
                twu_add = 0.0
                for tx_items, tu in tu_list:
                    if contains_itemset(tx_items, pair):
                        twu_add += tu
                if twu_add > 0.0:
                    entry.twu_per_partition[p_idx] = entry.twu_per_partition.get(p_idx, 0.0) + twu_add
                    entry.refresh_totals()

            # Prune CF by cumulative thresholds up to current partition
            to_delete = []
            for itemset, entry in cf.items():
                thr = entry.cumulative_threshold(s_part, p_idx)
                if entry.twu_total < thr:
                    to_delete.append(itemset)
            for iset in to_delete:
                del cf[iset]

        # At this point, CF holds the progressive temporal-high TWU 2-itemsets over db1,n (Thtw1,n).
        twu2i: Set[FrozenSet[str]] = set(cf.keys())

        # Scan-reduction: generate higher-order candidates C_k (k>=3) from TWU2I
        candidate_sets: List[Set[FrozenSet[str]]] = []
        k = 3
        while True:
            ck = candidate_join_from_twu2i(twu2i, k) if twu2i else set()
            if not ck:
                break
            candidate_sets.append(ck)
            k += 1

        # Final pass: compute exact utility u(X) for all candidates in {high 1-items} U TWU2I U {C_k}
        all_candidates: Set[FrozenSet[str]] = set()
        all_candidates |= {frozenset([i]) for i in twu1_high}
        all_candidates |= twu2i
        for ck in candidate_sets:
            all_candidates |= ck

        thut: Dict[FrozenSet[str], float] = defaultdict(float)
        # One full scan across the entire initial window
        for part in partitions:
            for tx in part:
                tx_items = items_in_tx(tx)
                if not tx_items:
                    continue
                # Precompute per-item utility for this tx to speed up u(X,T) calculation
                item_u = {i: tx.get(i, 0.0) * self.utilities.get(i, 0.0) for i in tx_items}
                for X in all_candidates:
                    if X.issubset(tx_items):
                        thut[X] += sum(item_u[i] for i in X)

        # Keep only those with u(X) >= e
        thut = {X: u for X, u in thut.items() if u >= self.e}

        return MiningResult(
            thut_itemsets=thut,
            cf=cf,
            twu1_high=twu1_high,
            num_partitions=n,
            s_global=self.e,
            s_part=s_part,
            utilities=self.utilities,
            window_partitions=[list(map(dict, part)) for part in partitions],  # shallow copy
        )

    # -------- Fig. 4: Incremental --------

    def incremental(self, state: MiningResult, delete_k: int, added_partitions: List[List[Dict[str, float]]]) -> MiningResult:
        """Slide the window from db_{m,n} to db_{i,j} by deleting the oldest `delete_k` partitions
        and appending new partitions.

        This implements Fig. 4 in three sub-steps:
        (1) reverse contributions from deleted partitions (update CF, shift start to next surviving partition index)
        (2) process the added partitions to update CF and prune by cumulative thresholds
        (3) one final scan over the new window to produce temporal high utility itemsets

        :param state: MiningResult from the previous window
        :param delete_k: number of oldest partitions to delete
        :param added_partitions: list of new partitions to append
        :return: updated MiningResult for the new window
        """
        old_parts = state.window_partitions
        assert 0 <= delete_k <= len(old_parts), "delete_k must be between 0 and the current number of partitions"
        # New window partitions
        new_parts = old_parts[delete_k:] + list(added_partitions)
        if not new_parts:
            # window is empty
            return MiningResult({}, {}, set(), 0, state.s_global, 0.0, state.utilities, [])

        # New parameters
        n_new = len(new_parts)
        s_part_new = state.s_global / n_new

        # 1) Reverse cumulative contributions for deletions in CF
        cf = state.cf  # mutate a copy
        cf = {k: CFEntry(start=v.start, twu_total=v.twu_total, twu_per_partition=dict(v.twu_per_partition)) for k, v in cf.items()}

        # deleted partition indices in the OLD indexing: 1..delete_k
        deleted_indices_old = set(range(1, delete_k + 1))

        # Map old partition index to new index (after deletion) for surviving partitions
        # Old index p in [delete_k+1 .. old_n] -> new index p' = p - delete_k
        def remap_index(old_idx: int) -> int:
            return old_idx - delete_k

        # First, drop TWU contributions from deleted partitions
        for itemset, entry in list(cf.items()):
            changed = False
            for p in list(entry.twu_per_partition.keys()):
                if p in deleted_indices_old:
                    del entry.twu_per_partition[p]
                    changed = True
            if changed:
                entry.refresh_totals()

            # Shift per-partition keys down by delete_k to align with new window indexing
            new_map = {}
            for p, val in entry.twu_per_partition.items():
                new_map[remap_index(p)] = val
            entry.twu_per_partition = new_map
            entry.refresh_totals()

            # Adjust start: if start <= delete_k, we set start=1 in the new window (first surviving partition)
            entry.start = max(1, entry.start - delete_k)

        # 2) Process added partitions (append to the right), update CF and prune per cumulative thresholds

        # First, compute high TWU 1-items for each new partition and also add 2-item candidates
        # We'll need transaction utility list for each new partition to compute 2-item TWU
        start_idx_for_new = n_new - len(added_partitions) + 1  # new index of first added partition
        # Build TU lists for all existing partitions as well, because we need to evaluate cumulative threshold at each step
        # For performance we only need TU lists for newly added partitions here.
        for offset, part in enumerate(added_partitions):
            p_idx_new = start_idx_for_new + offset

            # Compute transaction utilities + 1-item TWU for this new partition
            tu_list: List[Tuple[Set[str], float]] = []
            twu1_this_part: Dict[str, float] = defaultdict(float)
            for tx in part:
                tx_items = items_in_tx(tx)
                if not tx_items:
                    continue
                tu = transaction_utility(tx, state.utilities)
                tu_list.append((tx_items, tu))
                for i in tx_items:
                    twu1_this_part[i] += tu

            # Identify high TWU 1-items in this new partition
            high1 = {i for i, val in twu1_this_part.items() if val >= s_part_new}

            # Generate (or update) 2-itemset entries from these high1 items
            for pair in power_join_pairs(high1):
                entry = cf.get(pair)
                if entry is None:
                    entry = CFEntry(start=p_idx_new)
                    cf[pair] = entry
                twu_add = 0.0
                for tx_items, tu in tu_list:
                    if contains_itemset(tx_items, pair):
                        twu_add += tu
                if twu_add > 0.0:
                    entry.twu_per_partition[p_idx_new] = entry.twu_per_partition.get(p_idx_new, 0.0) + twu_add
                    entry.refresh_totals()

            # After incorporating THIS new partition, prune by cumulative threshold at p_idx_new
            to_delete = []
            for itemset, entry in cf.items():
                thr = entry.cumulative_threshold(s_part_new, p_idx_new)
                if entry.twu_total < thr:
                    to_delete.append(itemset)
            for iset in to_delete:
                del cf[iset]

        # 3) Final scan over the new window to compute exact utility for candidates:
        # - 1-itemsets that are currently high TWU (we re-evaluate globally across the new window)
        # - 2-itemsets in CF (temporal high TWU 2-itemsets)
        # - higher-order candidates built from TWU2I
        # First compute global high TWU 1-items for the *entire new window*
        twu1_global: Dict[str, float] = defaultdict(float)
        for part in new_parts:
            for tx in part:
                tx_items = items_in_tx(tx)
                if not tx_items:
                    continue
                tu = transaction_utility(tx, state.utilities)
                for i in tx_items:
                    twu1_global[i] += tu
        twu1_high_new = {i for i, val in twu1_global.items() if val >= s_part_new}

        # TWU2I = keys of CF
        twu2i: Set[FrozenSet[str]] = set(cf.keys())

        # Generate higher-order candidates via join
        candidate_sets: List[Set[FrozenSet[str]]] = []
        k = 3
        while True:
            ck = candidate_join_from_twu2i(twu2i, k) if twu2i else set()
            if not ck:
                break
            candidate_sets.append(ck)
            k += 1

        # Candidate universe for exact utility
        candidate_all: Set[FrozenSet[str]] = set()
        candidate_all |= {frozenset([i]) for i in twu1_high_new}
        candidate_all |= twu2i
        for ck in candidate_sets:
            candidate_all |= ck

        thut: Dict[FrozenSet[str], float] = defaultdict(float)
        for part in new_parts:
            for tx in part:
                tx_items = items_in_tx(tx)
                if not tx_items:
                    continue
                item_u = {i: tx.get(i, 0.0) * state.utilities.get(i, 0.0) for i in tx_items}
                for X in candidate_all:
                    if X.issubset(tx_items):
                        thut[X] += sum(item_u[i] for i in X)

        # Keep only those with u(X) >= e
        thut = {X: u for X, u in thut.items() if u >= state.s_global}

        return MiningResult(
            thut_itemsets=thut,
            cf=cf,
            twu1_high=twu1_high_new,
            num_partitions=n_new,
            s_global=state.s_global,
            s_part=s_part_new,
            utilities=state.utilities,
            window_partitions=[list(map(dict, part)) for part in new_parts],
        )


# -----------------------------
# Utilities to help users build inputs
# -----------------------------

def make_partition(transactions: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """Helper to ensure correct structure for a partition."""
    return [dict(tx) for tx in transactions]


def example_usage() -> None:
    """Small end-to-end smoke test on the paper's toy example.
    This is not a strict reproduction of all numbers in the text, but shows how to call the API.
    """
    # Utility table (Table 1b)
    utilities = {"A": 3, "B": 10, "C": 1, "D": 6, "E": 5}
    # Transactions (Table 1a) rewritten as dicts (omit items with qty 0 for brevity)
    T1 = {"C": 26, "E": 1}
    T2 = {"B": 6, "D": 1, "E": 1}
    T3 = {"A": 12, "D": 1}
    T4 = {"B": 1, "D": 7}
    T5 = {"C": 12, "E": 2}
    T6 = {"A": 1, "B": 4, "E": 1}
    T7 = {"B": 10, "E": 1}
    T8 = {"A": 1, "C": 1, "D": 3, "E": 1}
    T9 = {"A": 1, "B": 1, "C": 27}
    T10 = {"B": 6, "C": 2}
    T11 = {"B": 3, "D": 2}
    T12 = {"B": 2, "C": 1}

    # db1,3 example with three partitions P1, P2, P3 (each having three transactions, as in the text)
    P1 = make_partition([T1, T2, T3])
    P2 = make_partition([T4, T5, T6])
    P3 = make_partition([T7, T8, T9])
    initial_window = [P1, P2, P3]

    # Set global threshold e = 120 (as used in the example narrative)
    miner = THUIMine(utilities, min_utility_global=120.0)
    result = miner.preprocess(initial_window)
    print("Preprocess THUI:", {tuple(sorted(k)): v for k, v in sorted(result.thut_itemsets.items())})

    # Slide to db2,4: delete P1, add P4 (T10,T11,T12)
    P4 = make_partition([T10, T11, T12])
    next_result = miner.incremental(result, delete_k=1, added_partitions=[P4])
    print("Incremental THUI:", {tuple(sorted(k)): v for k, v in sorted(next_result.thut_itemsets.items())})


if __name__ == "__main__":
    example_usage()
