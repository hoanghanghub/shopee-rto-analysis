"""
main.py — Chạy toàn bộ pipeline phân tích RTO.

Chỉ cần chạy: py main.py
Output:
    - Bảng dòng tiền cơ sở (in ra terminal)
    - NPV, IRR, Payback (in ra terminal)
    - Kết quả Monte Carlo (in ra terminal)
    - VaR 95%, P(NPV<0), Break-even (in ra terminal)
    - Sensitivity analysis (in ra terminal)
    - Biểu đồ PNG lưu vào outputs/figures/
    - Kết quả JSON lưu vào outputs/results.json
"""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src import config
from src.analysis import (
    breakeven_rto_reduction,
    calc_probability_loss,
    calc_var,
    npv_at_rto_reduction,
    sensitivity_one_way,
)
from src.cashflow_model import build_cashflow_table, summarize_results
from src.data_loader import load_all_params
from src.monte_carlo import run_monte_carlo
from src.visualization import (
    plot_breakeven_curve,
    plot_npv_distribution,
    plot_sensitivity_tornado,
)


# ============================================================
# HELPER
# ============================================================


def print_section(title: str) -> None:
    """In tiêu đề section cho gọn gàng."""
    print()
    print("=" * 78)
    print(f"  {title}")
    print("=" * 78)


def save_results_json(results: dict, path: Path) -> None:
    """Lưu kết quả tổng hợp dạng JSON."""
    # Convert numpy types → Python native
    serializable = {}
    for k, v in results.items():
        if isinstance(v, (np.floating, np.integer)):
            serializable[k] = float(v)
        elif isinstance(v, dict):
            serializable[k] = {
                kk: float(vv) if isinstance(vv, (np.floating, np.integer)) else vv
                for kk, vv in v.items()
            }
        else:
            serializable[k] = v

    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Đã lưu: {path}")


# ============================================================
# MAIN PIPELINE
# ============================================================


def main() -> None:
    t_start = time.time()

    # Chuẩn bị thư mục output
    config.ensure_output_dirs()

    print()
    print("╔" + "═" * 76 + "╗")
    print("║" + " " * 16 + "SHOPEE XPRESS — RTO CAPITAL BUDGETING" + " " * 22 + "║")
    print("║" + " " * 20 + "Monte Carlo Simulation Pipeline" + " " * 24 + "║")
    print("╚" + "═" * 76 + "╝")

    # ----------------------------------------------------------
    # BƯỚC 1: LOAD PARAMS
    # ----------------------------------------------------------
    print_section("BƯỚC 1 — Đọc tham số từ Excel")
    params = load_all_params()
    print(f"  ✓ Đã đọc {len(params)} tham số từ: {config.EXCEL_FILE.name}")
    print(f"  • CF₀                       : {params['cf0_total']:>20,.0f} VNĐ")
    print(f"  • WACC                      : {params['wacc'] * 100:>19.1f} %")
    print(f"  • Baseline RTO              : {params['baseline_rto_rate'] * 100:>19.1f} %")
    print(f"  • Mức giảm RTO (mean)       : {params['rto_reduction_mean'] * 100:>19.1f} %")
    print(f"  • Số đơn COD/tháng          : {params['cod_orders_per_month']:>20,.0f}")

    # ----------------------------------------------------------
    # BƯỚC 2: DÒNG TIỀN CƠ SỞ
    # ----------------------------------------------------------
    print_section("BƯỚC 2 — Bảng dòng tiền cơ sở (Base Case)")
    table = build_cashflow_table(params)

    display_cols = ["Year 0", "Year 1", "Year 2", "Year 3"]
    rows_to_show = [
        "rto_prevented",
        "cash_inflow",
        "opex",
        "ebit",
        "tax",
        "net_cf",
        "cumulative_net_cf",
        "discounted_cf",
        "cumulative_discounted_cf",
    ]
    pd.set_option("display.float_format", lambda x: f"{x:>18,.0f}")
    pd.set_option("display.width", 200)
    print(table.loc[rows_to_show, display_cols].to_string())

    cashflows = list(table.loc["net_cf", :].values)
    base_results = summarize_results(cashflows, wacc=float(params["wacc"]))

    print()
    print(f"  NPV            : {base_results['npv']:>20,.0f} VNĐ")
    print(f"  IRR            : {base_results['irr'] * 100:>19.2f} %")
    print(f"  Payback        : {base_results['payback_years']:>19.2f} năm")

    # ----------------------------------------------------------
    # BƯỚC 3: MONTE CARLO
    # ----------------------------------------------------------
    print_section(f"BƯỚC 3 — Monte Carlo Simulation ({config.MONTE_CARLO_ITERATIONS} kịch bản)")
    print("  Đang chạy mô phỏng...")
    df_mc = run_monte_carlo(params, n_iter=config.MONTE_CARLO_ITERATIONS)
    npv_arr = df_mc["npv"].values
    print(f"  ✓ Xong ({len(df_mc)} kịch bản)")

    # ----------------------------------------------------------
    # BƯỚC 4: PHÂN TÍCH RỦI RO
    # ----------------------------------------------------------
    print_section("BƯỚC 4 — Phân tích rủi ro")
    prob_loss = calc_probability_loss(npv_arr)
    var_95 = calc_var(npv_arr, confidence=config.CONFIDENCE_LEVEL_VAR)
    print(f"  P(NPV < 0)               : {prob_loss * 100:>19.2f} %")
    print(f"  P(NPV > 0)               : {(1 - prob_loss) * 100:>19.2f} %")
    print(f"  VaR 95%                  : {var_95:>20,.0f} VNĐ")
    print(f"  NPV mean                 : {npv_arr.mean():>20,.0f} VNĐ")
    print(f"  NPV median               : {np.median(npv_arr):>20,.0f} VNĐ")
    print(f"  NPV std                  : {npv_arr.std():>20,.0f} VNĐ")
    print(f"  NPV min                  : {npv_arr.min():>20,.0f} VNĐ")
    print(f"  NPV max                  : {npv_arr.max():>20,.0f} VNĐ")

    # ----------------------------------------------------------
    # BƯỚC 5: BREAK-EVEN
    # ----------------------------------------------------------
    print_section("BƯỚC 5 — Break-even Analysis")
    breakeven = breakeven_rto_reduction(params)
    if np.isnan(breakeven):
        print("  ⚠ Không có ngưỡng hòa vốn trong [0%, 99%]")
    else:
        print(f"  Ngưỡng hòa vốn (RTO reduction) : {breakeven * 100:>19.2f} %")
        print(f"  → Cần giảm ≥ {breakeven * 100:.2f}% số đơn RTO để NPV ≥ 0")
        p_above = (df_mc["rto_reduction"] >= breakeven).mean()
        print(f"  Xác suất đạt ngưỡng (từ MC)   : {p_above * 100:>19.2f} %")

    # ----------------------------------------------------------
    # BƯỚC 6: SENSITIVITY
    # ----------------------------------------------------------
    print_section("BƯỚC 6 — Sensitivity Analysis 1 chiều")
    df_sens_rto = sensitivity_one_way(params, "rto_reduction")
    df_sens_cod = sensitivity_one_way(params, "cod_orders")
    for label, df_s in [("rto_reduction", df_sens_rto), ("cod_orders", df_sens_cod)]:
        rng = df_s["npv"].max() - df_s["npv"].min()
        print(f"  • {label:20s}  NPV range: {df_s['npv'].min():>15,.0f} → {df_s['npv'].max():>15,.0f}  (Δ = {rng:>15,.0f})")

    # ----------------------------------------------------------
    # BƯỚC 7: VẼ BIỂU ĐỒ
    # ----------------------------------------------------------
    print_section("BƯỚC 7 — Vẽ biểu đồ")
    plot_npv_distribution(npv_arr, var_95=var_95, breakeven=0.0)

    plot_sensitivity_tornado(
        df_sens_rto, df_sens_cod, base_npv=base_results["npv"]
    )

    # Curve NPV theo mức giảm RTO
    rto_range = np.linspace(0.01, 0.80, 50)
    npv_values = np.array([npv_at_rto_reduction(r, params) for r in rto_range])
    if not np.isnan(breakeven):
        plot_breakeven_curve(rto_range, npv_values, breakeven)

    # ----------------------------------------------------------
    # BƯỚC 8: LƯU KẾT QUẢ JSON
    # ----------------------------------------------------------
    print_section("BƯỚC 8 — Lưu kết quả")
    summary = {
        "base_case": {
            "npv": base_results["npv"],
            "irr": base_results["irr"],
            "payback_years": base_results["payback_years"],
        },
        "monte_carlo": {
            "n_iterations": len(df_mc),
            "npv_mean": float(npv_arr.mean()),
            "npv_median": float(np.median(npv_arr)),
            "npv_std": float(npv_arr.std()),
            "npv_min": float(npv_arr.min()),
            "npv_max": float(npv_arr.max()),
            "prob_loss": prob_loss,
            "var_95": var_95,
        },
        "breakeven": {
            "rto_reduction_threshold": (
                float(breakeven) if not np.isnan(breakeven) else None
            ),
            "prob_above_threshold": (
                float((df_mc["rto_reduction"] >= breakeven).mean())
                if not np.isnan(breakeven)
                else None
            ),
        },
    }
    save_results_json(summary, config.OUTPUTS_DIR / "results.json")

    # ----------------------------------------------------------
    # DONE
    # ----------------------------------------------------------
    elapsed = time.time() - t_start
    print()
    print("╔" + "═" * 76 + "╗")
    print("║" + f"  ✓ PIPELINE HOÀN TẤT — Thời gian chạy: {elapsed:.1f} giây".ljust(76) + "║")
    print("╚" + "═" * 76 + "╝")
    print()
    print("Kết quả đã lưu tại:")
    print(f"  • {config.FIGURES_DIR}")
    print(f"  • {config.OUTPUTS_DIR / 'results.json'}")


if __name__ == "__main__":
    main()