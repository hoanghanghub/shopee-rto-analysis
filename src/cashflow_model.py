"""
cashflow_model.py — Mô hình dòng tiền cơ sở cho dự án RTO.

Cung cấp 3 hàm chính:
    - build_cashflow_table(): Dựng bảng dòng tiền 3 năm
    - calc_npv(): Tính NPV
    - calc_irr(): Tính IRR
    - calc_payback(): Tính thời gian hoàn vốn
"""

from typing import Any

import numpy as np
import numpy_financial as npf
import pandas as pd


# ============================================================
# HÀM CHÍNH: DỰNG BẢNG DÒNG TIỀN
# ============================================================


def build_cashflow_table(
    params: dict[str, Any],
    rto_reduction: float | None = None,
    cod_orders_per_month: float | None = None,
) -> pd.DataFrame:
    """Dựng bảng dòng tiền 3 năm + Year 0.

    Args:
        params: Dict tham số từ data_loader.
        rto_reduction: Mức giảm RTO (override rto_reduction_mean nếu có).
        cod_orders_per_month: Số đơn COD/tháng (override nếu có).

    Returns:
        DataFrame với cột [Year 0, Year 1, Year 2, Year 3] và index là các
        chỉ tiêu: CashInflow, OpEx, EBIT, Tax, NetCF, ...
    """
    # --- Lấy tham số ---
    cf0 = float(params["cf0_total"])
    wacc = float(params["wacc"])
    tax_rate = float(params["corporate_tax_rate"])
    baseline_rto = float(params["baseline_rto_rate"])
    cost_saved = float(params["cost_saved_per_prevented_rto"])
    opex_zalo = float(params["opex_zalo_oa_annual"])
    depreciation = float(params["depreciation_annual"])
    growth_rate = float(params["order_growth_rate"])
    opex_growth = float(params["opex_growth_rate"])
    lifetime = int(params["project_lifetime"])

    # Override nếu có (dùng cho Monte Carlo)
    rto_red = rto_reduction if rto_reduction is not None else float(params["rto_reduction_mean"])
    cod_orders = (
        cod_orders_per_month
        if cod_orders_per_month is not None
        else float(params["cod_orders_per_month"])
    )

    # --- Dựng bảng cho Year 1..N ---
    years_data: dict[str, list[float]] = {
        "cod_orders_per_month": [],
        "rto_baseline": [],
        "rto_prevented": [],
        "cash_inflow": [],
        "opex": [],
        "depreciation": [],
        "ebit": [],
        "tax": [],
        "pat": [],
        "net_cf": [],
    }

    for year in range(1, lifetime + 1):
        cod_y = cod_orders * (1 + growth_rate) ** (year - 1)
        rto_base_y = cod_y * baseline_rto * 12
        rto_prev_y = rto_base_y * rto_red
        inflow_y = rto_prev_y * cost_saved
        opex_y = opex_zalo * (1 + opex_growth) ** (year - 1)
        ebit_y = inflow_y - opex_y - depreciation
        tax_y = max(0.0, ebit_y) * tax_rate
        pat_y = ebit_y - tax_y
        net_cf_y = pat_y + depreciation

        years_data["cod_orders_per_month"].append(cod_y)
        years_data["rto_baseline"].append(rto_base_y)
        years_data["rto_prevented"].append(rto_prev_y)
        years_data["cash_inflow"].append(inflow_y)
        years_data["opex"].append(opex_y)
        years_data["depreciation"].append(depreciation)
        years_data["ebit"].append(ebit_y)
        years_data["tax"].append(tax_y)
        years_data["pat"].append(pat_y)
        years_data["net_cf"].append(net_cf_y)

    # --- Ghép Year 0 ---
    columns = ["Year 0"] + [f"Year {y}" for y in range(1, lifetime + 1)]

    table: dict[str, list[float]] = {}

    for key, values in years_data.items():
        table[key] = [np.nan] + values  # Year 0 không có giá trị cho các dòng này

    # Net Cash Flow của Year 0 = -CF0
    table["net_cf"][0] = -cf0

    # Cumulative Net CF
    cum_ncf = list(np.cumsum(table["net_cf"]))
    table["cumulative_net_cf"] = cum_ncf

    # Discounted CF
    discount_factors = [1.0] + [(1 + wacc) ** y for y in range(1, lifetime + 1)]
    discounted_cf = [ncf / df for ncf, df in zip(table["net_cf"], discount_factors)]
    table["discounted_cf"] = discounted_cf

    # Cumulative Discounted CF (= NPV theo từng năm)
    table["cumulative_discounted_cf"] = list(np.cumsum(discounted_cf))

    df = pd.DataFrame(table, index=columns).T
    df.columns.name = "Indicator"
    return df


# ============================================================
# CÁC CHỈ TIÊU TÀI CHÍNH
# ============================================================


def calc_npv(cashflows: list[float], wacc: float) -> float:
    """Tính NPV từ list dòng tiền (bao gồm Year 0 âm)."""
    return float(npf.npv(wacc, cashflows))


def calc_irr(cashflows: list[float]) -> float:
    """Tính IRR. Trả về np.nan nếu không có nghiệm."""
    irr = npf.irr(cashflows)
    return float(irr) if not np.isnan(irr) else np.nan


def calc_payback(cashflows: list[float]) -> float:
    """Tính thời gian hoàn vốn (đơn vị: năm).

    Trả về np.inf nếu không hoàn vốn được trong vòng đời dự án.
    """
    cumulative = np.cumsum(cashflows)
    for i, cum in enumerate(cumulative):
        if cum >= 0 and i > 0:
            prev_cum = cumulative[i - 1]
            cf_i = cashflows[i]
            # Thời gian trong năm thứ i
            frac = -prev_cum / cf_i if cf_i != 0 else 0
            return float(i - 1 + frac)
    return float("inf")


def summarize_results(cashflows: list[float], wacc: float) -> dict[str, float]:
    """Tính tất cả chỉ tiêu và trả về dict gọn gàng."""
    return {
        "npv": calc_npv(cashflows, wacc),
        "irr": calc_irr(cashflows),
        "payback_years": calc_payback(cashflows),
    }


# ============================================================
# CHẠY TRỰC TIẾP ĐỂ TEST
# ============================================================

if __name__ == "__main__":
    from src.data_loader import load_all_params

    params = load_all_params()
    table = build_cashflow_table(params)

    pd.set_option("display.float_format", lambda x: f"{x:,.2f}")
    pd.set_option("display.width", 180)

    print("=" * 80)
    print("BẢNG DÒNG TIỀN CƠ SỞ (Base Case)")
    print("=" * 80)
    print(table.to_string())
    print()

    # Tính NPV/IRR/Payback
    cashflows = list(table.loc["net_cf", :].values)
    results = summarize_results(cashflows, wacc=float(params["wacc"]))

    print("=" * 80)
    print("KẾT QUẢ TÀI CHÍNH")
    print("=" * 80)
    print(f"  NPV            : {results['npv']:>20,.0f} VNĐ")
    print(f"  IRR            : {results['irr'] * 100:>19.2f} %")
    print(f"  Payback        : {results['payback_years']:>19.2f} năm")