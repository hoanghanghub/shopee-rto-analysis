"""
config.py — Cấu hình toàn cục cho project Shopee Xpress RTO Analysis.

File này chứa:
    - Đường dẫn tới file Excel dữ liệu
    - Đường dẫn tới các thư mục output
    - Các hằng số dùng chung cho mô hình tài chính
    - Hàm tiện ích để tạo đường dẫn an toàn
"""

from pathlib import Path

# ============================================================
# ĐƯỜNG DẪN GỐC CỦA PROJECT
# ============================================================

# Path(__file__).parent = thư mục src/
# .parent = thư mục gốc project
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"

OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"
FIGURES_DIR: Path = OUTPUTS_DIR / "figures"
TABLES_DIR: Path = OUTPUTS_DIR / "tables"

# ============================================================
# FILE DỮ LIỆU ĐẦU VÀO
# ============================================================

EXCEL_FILE: Path = RAW_DATA_DIR / "ShopeeXpress_RTO_Model.xlsx"
SHEET_ASSUMPTIONS: str = "00_Assumptions"
SHEET_ZALO_OA: str = "Zalo OA cost"
SHEET_CASHFLOW: str = "03_CashFlow"

# ============================================================
# HẰNG SỐ MÔ HÌNH TÀI CHÍNH
# ============================================================

PROJECT_LIFETIME_YEARS: int = 3          # Số năm dự án
MONTE_CARLO_ITERATIONS: int = 1000       # Số kịch bản Monte Carlo
CONFIDENCE_LEVEL_VAR: float = 0.95       # Mức tin cậy cho VaR
RANDOM_SEED: int = 42                    # Seed để tái lập kết quả

# ============================================================
# HÀM TIỆN ÍCH
# ============================================================


def ensure_output_dirs() -> None:
    """Tạo các thư mục output nếu chưa tồn tại."""
    for directory in (FIGURES_DIR, TABLES_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def validate_excel_exists() -> None:
    """Raise lỗi rõ ràng nếu file Excel không tồn tại."""
    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file Excel tại: {EXCEL_FILE}\n"
            f"Vui lòng đặt file 'ShopeeXpress_RTO_Model.xlsx' "
            f"vào thư mục: {RAW_DATA_DIR}"
        )


# ============================================================
# KIỂM TRA KHI CHẠY TRỰC TIẾP
# ============================================================

if __name__ == "__main__":
    print("PROJECT_ROOT      :", PROJECT_ROOT)
    print("EXCEL_FILE        :", EXCEL_FILE)
    print("EXCEL exists?     :", EXCEL_FILE.exists())
    print("FIGURES_DIR       :", FIGURES_DIR)
    print("TABLES_DIR        :", TABLES_DIR)
    print()
    print("Hằng số mô hình:")
    print("  LIFETIME (năm)  :", PROJECT_LIFETIME_YEARS)
    print("  MC ITERATIONS   :", MONTE_CARLO_ITERATIONS)
    print("  VAR CONFIDENCE  :", CONFIDENCE_LEVEL_VAR)
    print("  RANDOM SEED     :", RANDOM_SEED)