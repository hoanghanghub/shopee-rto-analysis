"""
analysis.py — Phân tích kết quả Monte Carlo.

Bao gồm:
    - calc_var(): VaR ở ngưỡng tin cậy 95%
    - calc_probability_loss(): Xác suất NPV < 0
    - breakeven_rto_reduction(): Tìm mức giảm RTO tối thiểu để NPV = 0
    - sensitivity_one_way(): Phân tích độ nhạy 1 chiều cho từng biến
"""

from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from src import config
from src.cashflow_model import build_cashflow_table, calc_npv
from src.data_loader import load_all_params


# ============================================================
# CHỈ TIÊU RỦI RO
# ============================================================


def calc_var(npv_array: np.ndarray, confidence: float = 0.95) -> float:
    """VaR ở ngưỡng tin cậy (mặc định 95%).

    VaR = percentile (1 - confidence) của phân phối NPV.
    Ví dụ: 95% tin cậy → lấy percentile 5 của NPV.

    Args:
        npv_array: Array NPV từ Monte Carlo.
        confidence: Mức tin cậy (0.95 = 95%).

    Returns:
        VaR (âm là lỗ).
    """
    return float(np.percentile(npv_array, (1 - confidence) * 100))


def calc_probability_loss(npv_array: np.ndarray) -> float:
    """Xác suất NPV < 0."""
    return float((npv_array < 0).mean())


def calc_probability_above_threshold(
    npv_array: np.ndarray, threshold: float = 0.0
) -> float:
    """Xác suất NPV > threshold (mặc định = 0)."""
    return float((npv_array > threshold).mean())


# ============================================================
# BREAK-EVEN ANALYSIS
# ============================================================


def npv_at_rto_reduction(
    rto_reduction: float,
    params: dict[str, Any],
    cod_orders_per_month: float | None = None,
) -> float:
    """Helper: tính NPV với rto_reduction cho trước, các biến khác ở mean."""
    table = build_cashflow_table(
        params,
        rto_reduction=rto_reduction,
        cod_orders_per_month=cod_orders_per_month,
    )
    cashflows = list(table.loc["net_cf", :].values)
    return calc_npv(cashflows, wacc=float(params["wacc"]))


def breakeven_rto_reduction(
    params: dict[str, Any],
    cod_orders_per_month: float | None = None,
    bounds: tuple[float, float] = (0.0, 0.99),
) -> float:
    """Tìm mức giảm RTO tối thiểu để NPV = 0 (giữ các biến khác ở mean).

    Dùng Brent's method để tìm nghiệm NPV(rto_reduction) = 0.

    Returns:
        Mức giảm RTO hòa vốn (dạng thập phân, ví dụ 0.152 = 15.2%).
        Trả về np.nan nếu không có nghiệm trong bounds.
    """
    def f(x: float) -> float:
        return npv_at_rto_reduction(x, params, cod_orders_per_month)

    try:
        return float(brentq(f, bounds[0], bounds[1], xtol=1e-6))
    except ValueError:
        # f(a) và f(b) cùng dấu → không có nghiệm
        return float("nan")


# ============================================================
# SENSITIVITY ANALYSIS 1 CHIỀU
# ============================================================


def sensitivity_one_way(
    params: dict[str, Any],
    var_name: str,
    multipliers: np.ndarray | None = None,
) -> pd.DataFrame:
    """Phân tích độ nhạy NPV theo 1 biến, các biến khác giữ ở giá trị mean.

    Args:
        params: Dict tham số.
        var_name: Tên biến cần phân tích:
            - "rto_reduction": mức giảm RTO (0-1)
            - "cod_orders": quy mô đơn COD/tháng
        multipliers: Mảng các hệ số nhân (mặc định từ 0.5 đến 1.5).

    Returns:
        DataFrame với cột [multiplier, value, npv].
    """
    if multipliers is None:
        multipliers = np.linspace(0.5, 1.5, 11)

    base_rto = float(params["rto_reduction_mean"])
    base_cod = float(params["cod_orders_per_month"])

    rows = []
    for m in multipliers:
        if var_name == "rto_reduction":
            value = base_rto * m
            # Không cho vượt 1.0
            value = min(value, 1.0)
            npv = npv_at_rto_reduction(value, params, base_cod)
        elif var_name == "cod_orders":
            value = base_cod * m
            npv = npv_at_rto_reduction(base_rto, params, value)
        else:
            raise ValueError(f"var_name không hợp lệ: {var_name}")

        rows.append({"multiplier": m, "value": value, "npv": npv})

    return pd.DataFrame(rows)


# ============================================================
# CHẠY TRỰC TIẾP ĐỂ TEST
# ============================================================

if __name__ == "__main__":
    from src.monte_carlo import run_monte_carlo

    params = load_all_params()

    # --- Monte Carlo để lấy array NPV ---
    print("Đang chạy Monte Carlo 1,000 kịch bản...")
    df_mc = run_monte_carlo(params, n_iter=1000)
    npv_arr = df_mc["npv"].values

    # --- Chỉ tiêu rủi ro ---
    print("\n" + "=" * 70)
    print("CHỈ TIÊU RỦI RO (Monte Carlo, N=1000)")
    print("=" * 70)
    prob_loss = calc_probability_loss(npv_arr)
    var_95 = calc_var(npv_arr, confidence=0.95)
    print(f"  P(NPV < 0)        : {prob_loss * 100:>6.2f} %")
    print(f"  P(NPV > 0)        : {(1 - prob_loss) * 100:>6.2f} %")
    print(f"  VaR 95%           : {var_95:>20,.0f} VNĐ")

    # --- Break-even ---
    print("\n" + "=" * 70)
    print("BREAK-EVEN ANALYSIS")
    print("=" * 70)
    be = breakeven_rto_reduction(params)
    if np.isnan(be):
        print("  Không có ngưỡng hòa vốn trong khoảng [0%, 99%]")
    else:
        print(f"  Ngưỡng hòa vốn (RTO reduction): {be * 100:>6.2f} %")
        print(f"  → Cần giảm ít nhất {be * 100:.2f}% số đơn RTO để NPV ≥ 0")

        # Xác suất đạt ngưỡng này
        p_above = (df_mc["rto_reduction"] >= be).mean()
        print(f"  Xác suất đạt ngưỡng (từ MC)    : {p_above * 100:>6.2f} %")

    # --- Sensitivity ---
    print("\n" + "=" * 70)
    print("SENSITIVITY ANALYSIS 1 CHIỀU")
    print("=" * 70)

    for var in ["rto_reduction", "cod_orders"]:
        print(f"\n--- Biến: {var} ---")
        df_sens = sensitivity_one_way(params, var)
        # Range NPV khi biến thay đổi ±50%
        npv_range = df_sens["npv"].max() - df_sens["npv"].min()
        print(f"  NPV range (min→max): {df_sens['npv'].min():,.0f} → {df_sens['npv'].max():,.0f}")
        print(f"  Tổng biên độ ảnh hưởng: {npv_range:>20,.0f} VNĐ")
        print(df_sens.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))