"""Standalone driver for executing the Two-Phase algorithm and saving results."""

from __future__ import annotations

from pathlib import Path

from algo_two_phase import AlgoTwoPhase
from utility_transaction_database_tp import UtilityTransactionDatabaseTP


def file_to_path(filename: str) -> Path:
    return Path(__file__).resolve().parent / filename


def main() -> None:
    input_path = file_to_path("new_DB_Utility.txt")
    output_path = Path("two_phase_output.txt")

    database = UtilityTransactionDatabaseTP()
    database.load_file(input_path)

    min_utility = 20
    algo = AlgoTwoPhase()
    high_utility_itemsets = algo.run_algorithm(database, min_utility)

    high_utility_itemsets.save_results_to_file(
        output_path, len(database.get_transactions())
    )
    algo.print_stats()


if __name__ == "__main__":
    main()
