"""
Simplified THUI-Mine: Temporal High Utility Itemset Mining

A streamlined implementation that mines itemsets with high utility 
over sliding time windows.

Key concepts:
- Transaction: items with quantities, e.g., {"A": 2, "B": 1}
- Utility: value of items (quantity × price)
- Window: set of partitions (time periods)
- High utility: itemsets meeting minimum utility threshold
"""

from collections import defaultdict
from itertools import combinations


class THUIMine:
    """Simple THUI-Mine implementation for temporal high utility itemset mining."""
    
    def __init__(self, item_prices, min_utility):
        """
        Args:
            item_prices: Dictionary mapping item names to their prices
            min_utility: Minimum utility threshold
        """
        self.prices = item_prices
        self.min_utility = min_utility
        self.window = []  # Current partitions in window
        
    def _transaction_utility(self, transaction):
        """Calculate total utility of a transaction."""
        return sum(qty * self.prices.get(item, 0) 
                   for item, qty in transaction.items())
    
    def _itemset_utility(self, itemset, transaction):
        """Calculate utility of an itemset in a transaction."""
        if not all(item in transaction for item in itemset):
            return 0
        return sum(transaction[item] * self.prices.get(item, 0) 
                   for item in itemset)
    
    def _get_high_twu_items(self, partitions, threshold):
        """Find items with Transaction-Weighted Utilization above threshold."""
        twu = defaultdict(float)
        
        for partition in partitions:
            for transaction in partition:
                tu = self._transaction_utility(transaction)
                for item in transaction:
                    twu[item] += tu
        
        return {item for item, value in twu.items() if value >= threshold}
    
    def _generate_candidates(self, high_items, max_size=10):
        """Generate candidate itemsets from high TWU items."""
        candidates = set()
        
        # Add 1-itemsets
        for item in high_items:
            candidates.add(frozenset([item]))
        
        # Add 2-itemsets and larger
        items_list = sorted(high_items)
        for size in range(2, min(len(items_list) + 1, max_size + 1)):
            for combo in combinations(items_list, size):
                candidates.add(frozenset(combo))
        
        return candidates
    
    def _mine_utilities(self, partitions, candidates):
        """Calculate exact utility for all candidates."""
        utilities = defaultdict(float)
        
        for partition in partitions:
            for transaction in partition:
                for candidate in candidates:
                    utility = self._itemset_utility(candidate, transaction)
                    utilities[candidate] += utility
        
        # Keep only high utility itemsets
        return {itemset: util for itemset, util in utilities.items() 
                if util >= self.min_utility}
    
    def mine(self, partitions):
        """
        Mine high utility itemsets from partitions.
        
        Args:
            partitions: List of partitions, where each partition is a list
                       of transactions (dicts mapping items to quantities)
        
        Returns:
            Dictionary mapping itemsets to their utilities
        """
        if not partitions:
            return {}
        
        self.window = partitions
        
        # Calculate per-partition threshold
        threshold = self.min_utility / len(partitions)
        
        # Find items with high TWU
        high_items = self._get_high_twu_items(partitions, threshold)
        
        # Generate candidates
        candidates = self._generate_candidates(high_items)
        
        # Calculate exact utilities
        return self._mine_utilities(partitions, candidates)
    
    def slide_window(self, delete_count, new_partitions):
        """
        Slide the window: remove old partitions and add new ones.
        
        Args:
            delete_count: Number of oldest partitions to remove
            new_partitions: New partitions to add
        
        Returns:
            Dictionary mapping itemsets to their utilities
        """
        # Update window
        self.window = self.window[delete_count:] + new_partitions
        
        # Re-mine on new window
        return self.mine(self.window)


# Example usage
def example():
    """Demonstrate THUI-Mine with a simple example."""
    
    # Item prices
    prices = {"A": 3, "B": 10, "C": 1, "D": 6, "E": 5}
    
    # Transactions (quantity per item)
    transactions = [
        {"C": 26, "E": 1},      # T1
        {"B": 6, "D": 1, "E": 1},  # T2
        {"A": 12, "D": 1},      # T3
        {"B": 1, "D": 7},       # T4
        {"C": 12, "E": 2},      # T5
        {"A": 1, "B": 4, "E": 1},  # T6
        {"B": 10, "E": 1},      # T7
        {"A": 1, "C": 1, "D": 3, "E": 1},  # T8
        {"A": 1, "B": 1, "C": 27},  # T9
        {"B": 6, "C": 2},       # T10
        {"B": 3, "D": 2},       # T11
        {"B": 2, "C": 1}        # T12
    ]
    
    # Split into partitions (3 transactions each)
    P1 = transactions[0:3]
    P2 = transactions[3:6]
    P3 = transactions[6:9]
    P4 = transactions[9:12]
    
    # Initialize miner
    miner = THUIMine(prices, min_utility=120.0)
    
    # Mine initial window (P1, P2, P3)
    print("Mining initial window [P1, P2, P3]...")
    result1 = miner.mine([P1, P2, P3])
    print(f"Found {len(result1)} high utility itemsets:")
    for itemset, utility in sorted(result1.items()):
        print(f"  {set(itemset)}: {utility:.1f}")
    
    # Slide window: remove P1, add P4
    print("\nSliding window to [P2, P3, P4]...")
    result2 = miner.slide_window(delete_count=1, new_partitions=[P4])
    print(f"Found {len(result2)} high utility itemsets:")
    for itemset, utility in sorted(result2.items()):
        print(f"  {set(itemset)}: {utility:.1f}")


if __name__ == "__main__":
    example()