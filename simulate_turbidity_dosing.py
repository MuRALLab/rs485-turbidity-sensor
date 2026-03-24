"""
Simulate turbidity dosing calculations for a series of target NTU values.

This script calculates the incremental stock solution required to achieve each target NTU, as well as the total stock added and the resulting total volume after dosing. It validates inputs and handles edge cases where targets are invalid or lower than previous steps.

"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DosingResult:
    target_ntu: float
    incremental_mL: float
    total_stock_mL: float
    total_volume_mL: float


# ----------------------------
# Validation functions
# ----------------------------

def validate_inputs(c_stock: float, v_water_ml: float):
    if c_stock <= 0:
        raise ValueError("Stock NTU must be positive")
    if v_water_ml <= 0:
        raise ValueError("Initial water volume must be positive")


def is_valid_target(c_target: float, c_stock: float) -> bool:
    if c_target <= 0:
        print(f"Skipping invalid target NTU: {c_target}")
        return False
    if c_target >= c_stock:
        print(f"Skipping: Target NTU ({c_target}) must be less than stock ({c_stock})")
        return False
    return True


# ----------------------------
# Core calculation functions
# ----------------------------

def compute_total_stock(c_target: float, c_stock: float, v_water_ml: float) -> float:
    return (c_target * v_water_ml) / (c_stock - c_target)


def compute_incremental_stock(total_stock: float, prev_total: float) -> float:
    return total_stock - prev_total


def compute_total_volume(v_water_ml: float, total_stock: float) -> float:
    return v_water_ml + total_stock


# ----------------------------
# Result builder
# ----------------------------

def build_result(
    c_target: float,
    incremental: float,
    total_stock: float,
    total_volume: float,
) -> DosingResult:
    return DosingResult(
        target_ntu=c_target,
        incremental_mL=incremental,
        total_stock_mL=total_stock,
        total_volume_mL=total_volume,
    )


# ----------------------------
# Printing functions
# ----------------------------

def print_header():
    print(f"{'Target NTU':<12} | {'Add to Pour (mL)':<18} | {'Total Poured (mL)':<18} | {'Total Volume (mL)':<18}")
    print("-" * 75)


def print_row(result: DosingResult):
    print(
        f"{result.target_ntu:<12.0f} | "
        f"{result.incremental_mL:<18.3f} | "
        f"{result.total_stock_mL:<18.3f} | "
        f"{result.total_volume_mL:<18.3f}"
    )


# ----------------------------
# Single step processor
# ----------------------------

def process_target(
    c_target: float,
    c_stock: float,
    v_water_ml: float,
    prev_total_stock: float,
) -> Optional[DosingResult]:

    if not is_valid_target(c_target, c_stock):
        return None

    total_stock = compute_total_stock(c_target, c_stock, v_water_ml)
    incremental = compute_incremental_stock(total_stock, prev_total_stock)

    if incremental < 0:
        print(f"Warning: target {c_target} is lower than previous step. Skipping.")
        return None

    total_volume = compute_total_volume(v_water_ml, total_stock)

    return build_result(c_target, incremental, total_stock, total_volume)


# ----------------------------
# Main orchestration
# ----------------------------

def simulate_turbidity_dosing(
    target_ntus: List[int],
    c_stock: float = 4000.0,
    v_water_ml: float = 100.0,
    verbose: bool = True,
) -> List[DosingResult]:

    validate_inputs(c_stock, v_water_ml)

    results: List[DosingResult] = []
    prev_total_stock = 0.0

    if verbose:
        print_header()

    for c_target in target_ntus:
        result = process_target(
            c_target,
            c_stock,
            v_water_ml,
            prev_total_stock,
        )

        if result is None:
            continue

        if verbose:
            print_row(result)

        results.append(result)
        prev_total_stock = result.total_stock_mL

    return results


# ----------------------------
# Entry point
# ----------------------------

if __name__ == "__main__":
    STOCK_NTU = 4000.0
    INITIAL_WATER_ML = 400.0
    TARGET_VALUES = [50, 100, 150, 200]

    simulate_turbidity_dosing(
        target_ntus=TARGET_VALUES,
        c_stock=STOCK_NTU,
        v_water_ml=INITIAL_WATER_ML,
        verbose=True,
    )