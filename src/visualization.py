"""
visualization.py — Vẽ biểu đồ cho báo cáo.

Bao gồm:
    - plot_npv_distribution(): Density plot phân phối NPV từ Monte Carlo
    - plot_sensitivity_tornado(): Tornado chart cho sensitivity 1 chiều
    - plot_breakeven_curve(): Đường NPV theo mức giảm RTO
"""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src import config


# Cấu hình style chung cho tất cả biểu đồ
sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["figure.dpi"] = 100
plt.rcParams["savefig.dpi"] = 150
plt.rcParams["font.family"] = "DejaVu Sans"


# ============================================================
# 1. DENSITY PLOT — PHÂN PHỐI NPV
# ============================================================


def plot_npv_distribution(
    npv_array: np.ndarray,
    var_95: float | None = None,
    breakeven: float = 0.0,
    save_path: str | None = None,
) -> None:
    """Vẽ density plot phân phối NPV từ Monte Carlo.

    Args:
        npv_array: Array NPV từ 1.000 kịch bản.
        var_95: VaR 95% (nếu có) để vẽ đường dọc.
        breakeven: Ngưỡng NPV hòa vốn (mặc định 0).
        save_path: Đường dẫn lưu file. Nếu None, dùng config.
    """
    if save_path is None:
        save_path = config.FIGURES_DIR / "npv_distribution.png"

    fig, ax = plt.subplots(figsize=(10, 6))

    # Histogram + KDE
    sns.histplot(
        npv_array,
        bins=40,
        kde=True,
        color="steelblue",
        edgecolor="white",
        linewidth=0.5,
        ax=ax,
        stat="density",
    )

    # Đường mean
    mean_npv = npv_array.mean()
    ax.axvline(
        mean_npv, color="green", linestyle="--", linewidth=2,
        label=f"Mean = {mean_npv:,.0f} VNĐ",
    )

    # Đường breakeven = 0
    ax.axvline(
        breakeven, color="black", linestyle="-", linewidth=2,
        label=f"Break-even (NPV = {breakeven:,.0f})",
    )

    # Đường VaR 95%
    if var_95 is not None:
        ax.axvline(
            var_95, color="red", linestyle="--", linewidth=2,
            label=f"VaR 95% = {var_95:,.0f} VNĐ",
        )

    # Vùng lỗ (NPV < 0)
    ax.axvspan(
        npv_array.min(), 0, alpha=0.10, color="red",
        label=f"Vùng lỗ ({(npv_array < 0).mean() * 100:.1f}% kịch bản)",
    )

    ax.set_xlabel("NPV (VNĐ)", fontsize=12)
    ax.set_ylabel("Mật độ xác suất", fontsize=12)
    ax.set_title(
        "Phân phối NPV từ Monte Carlo (1,000 kịch bản)",
        fontsize=14, fontweight="bold",
    )
    ax.legend(loc="upper left", fontsize=10)

    # Format trục x theo triệu VNĐ
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x / 1e6:,.0f}M")
    )

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Đã lưu: {save_path}")


# ============================================================
# 2. TORNADO CHART — SENSITIVITY
# ============================================================


def plot_sensitivity_tornado(
    df_rto: pd.DataFrame,
    df_cod: pd.DataFrame,
    base_npv: float,
    save_path: str | None = None,
) -> None:
    """Vẽ Tornado chart cho 2 biến sensitivity.

    Args:
        df_rto: DataFrame sensitivity của biến rto_reduction.
        df_cod: DataFrame sensitivity của biến cod_orders.
        base_npv: NPV cơ sở (tại multiplier = 1.0).
        save_path: Đường dẫn lưu file.
    """
    if save_path is None:
        save_path = config.FIGURES_DIR / "sensitivity_tornado.png"

    fig, ax = plt.subplots(figsize=(10, 5))

    # Với mỗi biến, lấy NPV tại multiplier = 0.5 và 1.5
    def get_low_high(df: pd.DataFrame) -> tuple[float, float]:
        low = df.loc[df["multiplier"].idxmin(), "npv"]
        high = df.loc[df["multiplier"].idxmax(), "npv"]
        return low, high

    rto_low, rto_high = get_low_high(df_rto)
    cod_low, cod_high = get_low_high(df_cod)

    # Vẽ các thanh ngang
    bar_height = 0.35
    y_positions = [1, 0]  # rto ở trên, cod ở dưới

    ax.barh(
        y_positions[0], rto_low - base_npv, height=bar_height,
        left=base_npv, color="firebrick", alpha=0.8,
        label="Giảm 50% biến",
    )
    ax.barh(
        y_positions[0], rto_high - base_npv, height=bar_height,
        left=base_npv, color="forestgreen", alpha=0.8,
        label="Tăng 50% biến",
    )
    ax.barh(
        y_positions[1], cod_low - base_npv, height=bar_height,
        left=base_npv, color="firebrick", alpha=0.8,
    )
    ax.barh(
        y_positions[1], cod_high - base_npv, height=bar_height,
        left=base_npv, color="forestgreen", alpha=0.8,
    )

    # Đường NPV cơ sở
    ax.axvline(
        base_npv, color="black", linestyle="--", linewidth=2,
        label=f"NPV cơ sở = {base_npv / 1e6:,.0f}M",
    )
    # Đường NPV = 0
    ax.axvline(0, color="gray", linestyle="-", linewidth=1, alpha=0.5)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(
        ["Mức giảm RTO\n(rto_reduction)", "Quy mô đơn\n(cod_orders)"],
        fontsize=11,
    )
    ax.set_xlabel("NPV (VNĐ)", fontsize=12)
    ax.set_title(
        "Sensitivity Analysis — Biến động ±50%",
        fontsize=14, fontweight="bold",
    )
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x / 1e6:,.0f}M")
    )
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Đã lưu: {save_path}")


# ============================================================
# 3. BREAK-EVEN CURVE
# ============================================================


def plot_breakeven_curve(
    rto_range: np.ndarray,
    npv_values: np.ndarray,
    breakeven: float,
    save_path: str | None = None,
) -> None:
    """Vẽ đường NPV theo mức giảm RTO.

    Args:
        rto_range: Mảng các mức giảm RTO (0..1).
        npv_values: NPV tương ứng.
        breakeven: Mức giảm RTO hòa vốn.
        save_path: Đường dẫn lưu file.
    """
    if save_path is None:
        save_path = config.FIGURES_DIR / "breakeven_curve.png"

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        rto_range * 100, npv_values / 1e6,
        color="steelblue", linewidth=2.5, label="NPV",
    )
    ax.axhline(0, color="black", linestyle="-", linewidth=1, alpha=0.6)
    ax.axvline(
        breakeven * 100, color="red", linestyle="--", linewidth=2,
        label=f"Ngưỡng hòa vốn = {breakeven * 100:.2f}%",
    )

    # Đánh dấu điểm giao
    ax.scatter(
        [breakeven * 100], [0], color="red", s=100, zorder=5,
        edgecolor="black", linewidth=1.5,
    )

    # Vùng lỗ / vùng lãi
    ax.fill_between(
        rto_range * 100, npv_values / 1e6, 0,
        where=(npv_values < 0), alpha=0.15, color="red", label="Lỗ",
    )
    ax.fill_between(
        rto_range * 100, npv_values / 1e6, 0,
        where=(npv_values >= 0), alpha=0.15, color="green", label="Lãi",
    )

    ax.set_xlabel("Mức giảm RTO (%)", fontsize=12)
    ax.set_ylabel("NPV (triệu VNĐ)", fontsize=12)
    ax.set_title(
        "Đường NPV theo mức giảm RTO — Break-even Analysis",
        fontsize=14, fontweight="bold",
    )
    ax.legend(loc="lower right", fontsize=11)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Đã lưu: {save_path}")