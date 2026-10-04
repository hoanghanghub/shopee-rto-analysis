"""
monte_carlo.py — Mô phỏng Monte Carlo cho mô hình dòng tiền RTO.

Sinh N kịch bản ngẫu nhiên cho 2 biến:
    - rto_reduction    ~ Beta(alpha, beta)
    - cod_orders       ~ Normal(mean, std)

Với mỗi cặp (rto_reduction, cod_orders), dựng bảng dòng tiền và tính NPV.
Trả về array NPV có shape (N,).
"""

from typing import Any

import numpy as np
import pandas as pd

from src import config
from src.cashflow_model import build_cashflow_table, summarize_results


# ============================================================
# HÀM CHÍNH
# ============================================================


def run_monte_carlo(
    params: dict[str, Any],
    n_iter: int | None = None,
    seed: int | None = None,
) -> pd.DataFrame:
    """Chạy Monte Carlo simulation.

    Args:
        params: Dict tham số.
        n_iter: Số kịch bản (mặc định lấy từ config).
        seed: Random seed để tái lập kết quả (None = random).

    Returns:
        DataFrame với các cột:
            - rto_reduction: mức giảm RTO đã sinh
            - cod_orders: quy mô đơn COD đã sinh
            - npv, irr, payback: chỉ tiêu tài chính
    """
    if n_iter is None:
        n_iter = config.MONTE_CARLO_ITERATIONS

    if seed is None:
        seed = config.RANDOM_SEED

    rng = np.random.default_rng(seed)

    # --- Lấy tham số ---
    alpha = float(params["beta_alpha"])
    beta = float(params["beta_beta"])
    cod_mean = float(params["cod_orders_per_month"])
    cod_std_ratio = float(params["order_volume_std"])
    cod_std = cod_mean * cod_std_ratio  # std tuyệt đối
    wacc = float(params["wacc"])

    # --- Sinh biến ngẫu nhiên ---
    rto_reductions = rng.beta(alpha, beta, size=n_iter)
    cod_orders_arr = rng.normal(cod_mean, cod_std, size=n_iter)

    # Đảm bảo cod_orders không âm (clip về 0 nếu lỡ âm)
    cod_orders_arr = np.maximum(cod_orders_arr, 0)

    # --- Vòng lặp tính NPV cho từng kịch bản ---
    npvs = np.empty(n_iter, dtype=float)
    irrs = np.empty(n_iter, dtype=float)
    paybacks = np.empty(n_iter, dtype=float)

    for i in range(n_iter):
        table = build_cashflow_table(
            params,
            rto_reduction=float(rto_reductions[i]),
            cod_orders_per_month=float(cod_orders_arr[i]),
        )
        cashflows = list(table.loc["net_cf", :].values)
        result = summarize_results(cashflows, wacc)

        npvs[i] = result["npv"]
        irrs[i] = result["irr"]
        paybacks[i] = result["payback_years"]

    # --- Đóng gói kết quả ---
    df_results = pd.DataFrame({
        "rto_reduction": rto_reductions,
        "cod_orders": cod_orders_arr,
        "npv": npvs,
        "irr": irrs,
        "payback": paybacks,
    })

    return df_results


# ============================================================
# CHẠY TRỰC TIẾP ĐỂ TEST
# ============================================================

if __name__ == "__main__":
    from src.data_loader import load_all_params

    params = load_all_params()
    df = run_monte_carlo(params, n_iter=1000)

    print("=" * 80)
    print("MONTE CARLO SIMULATION — 1,000 kịch bản")
    print("=" * 80)
    print(df.describe().to_string())
    print()

    # Đếm số kịch bản NPV âm
    n_negative = (df["npv"] < 0).sum()
    pct_negative = n_negative / len(df) * 100
    print(f"Số kịch bản NPV âm     : {n_negative} / {len(df)} ({pct_negative:.1f}%)")

    # VaR 95%
    var_95 = np.percentile(df["npv"], 5)
    print(f"VaR 95% (NPV percentile 5): {var_95:>20,.0f} VNĐ")
    print()

    # NPV mean
    print(f"NPV trung bình          : {df['npv'].mean():>20,.0f} VNĐ")
    print(f"NPV median              : {df['npv'].median():>20,.0f} VNĐ")
    print(f"NPV min / max           : {df['npv'].min():,.0f} / {df['npv'].max():,.0f} VNĐ")