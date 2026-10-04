"""
data_loader.py — Đọc dữ liệu từ file Excel và chuyển thành dict params.

Cách dùng:
    from src.data_loader import load_all_params
    params = load_all_params()
    cf0 = params["cf0_total"]
"""

from typing import Any

import pandas as pd

from src import config


# ============================================================
# HÀM NỘI BỘ: TÌM DÒNG HEADER
# ============================================================


def _find_header_row(df_raw: pd.DataFrame, key: str = "var_id") -> int:
    """Tìm dòng chứa tên cột `key` trong bảng Excel thô.

    Args:
        df_raw: DataFrame đọc từ Excel không có header.
        key: Tên cột cần tìm (mặc định "var_id").

    Returns:
        Index của dòng header (0-based).

    Raises:
        ValueError: Nếu không tìm thấy cột.
    """
    for idx, row in df_raw.iterrows():
        if key in row.values:
            return int(idx)
    raise ValueError(f"Không tìm thấy dòng header chứa cột '{key}'")


# ============================================================
# HÀM CHÍNH: ĐỌC 1 SHEET THÀNH DICT
# ============================================================


def load_sheet_as_params(
    filepath: str,
    sheet_name: str,
    id_col: str = "var_id",
    value_col: str = "value",
) -> dict[str, Any]:
    """Đọc 1 sheet Excel và trả về dict {var_id: value}.

    Args:
        filepath: Đường dẫn file Excel.
        sheet_name: Tên sheet cần đọc.
        id_col: Tên cột chứa mã biến.
        value_col: Tên cột chứa giá trị.

    Returns:
        Dictionary ánh xạ var_id → value.
    """
    # Bước 1: Đọc thô để tìm header row
    df_raw = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
    header_row = _find_header_row(df_raw, key=id_col)

    # Bước 2: Đọc lại với header đúng
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row)

    # Bước 3: Bỏ dòng thiếu var_id hoặc value
    df = df.dropna(subset=[id_col, value_col])

    # Bước 4: Chuyển thành dict
    params = dict(zip(df[id_col].astype(str).str.strip(), df[value_col]))

    return params


# ============================================================
# HÀM TỔNG: LOAD TẤT CẢ PARAMS CẦN THIẾT
# ============================================================


def load_all_params() -> dict[str, Any]:
    """Load và gộp tất cả params từ 2 sheet cần thiết.

    Returns:
        Dict gộp từ sheet 00_Assumptions và Zalo OA cost.
    """
    config.validate_excel_exists()

    # Load sheet assumptions
    params_assumptions = load_sheet_as_params(
        filepath=config.EXCEL_FILE,
        sheet_name=config.SHEET_ASSUMPTIONS,
    )

    # Load sheet Zalo OA cost
    params_zalo = load_sheet_as_params(
        filepath=config.EXCEL_FILE,
        sheet_name=config.SHEET_ZALO_OA,
    )

    # Gộp lại (nếu trùng key, ưu tiên sheet Zalo)
    params = {**params_assumptions, **params_zalo}

    return params


# ============================================================
# CHẠY TRỰC TIẾP ĐỂ TEST
# ============================================================

if __name__ == "__main__":
    params = load_all_params()

    print(f"Tổng số params đọc được: {len(params)}\n")

    # In một số key quan trọng để kiểm tra
    important_keys = [
        "cf0_total",
        "wacc",
        "corporate_tax_rate",
        "baseline_rto_rate",
        "rto_reduction_mean",
        "rto_reduction_std",
        "cod_orders_per_month",
        "cost_saved_per_prevented_rto",
        "opex_zalo_oa_annual",
        "depreciation_annual",
        "beta_alpha",
        "beta_beta",
        "project_lifetime",
        "mc_iterations",
    ]

    print("Các params quan trọng:")
    print("-" * 60)
    for key in important_keys:
        value = params.get(key, "<KHÔNG TÌM THẤY>")
        print(f"  {key:35s} = {value}")