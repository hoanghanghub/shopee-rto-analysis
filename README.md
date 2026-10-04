# Shopee Xpress RTO Reduction — Capital Budgeting & Monte Carlo

Mô hình đánh giá quyết định đầu tư hệ thống xác nhận đơn hàng tự động qua
Zalo OA kết hợp AI gợi ý khung giờ giao, nhằm giảm tỷ lệ Return-to-Origin
(RTO) tại Shopee Xpress Việt Nam.

**Vấn đề:** RTO là điểm nghẽn chi phí lớn của ngành TMĐT Việt Nam, đặc biệt
với đơn COD. Mỗi đơn hoàn phát sinh phí ship chiều đi + chi phí phân loại
lại tại kho — đều là chi phí chìm không thu hồi được. Nếu giảm được một
phần tỷ lệ này bằng xác nhận đơn tự động, tác động lên dòng tiền là trực tiếp
và đo lường được.

**Điểm khác biệt:** Đây không phải bài toán vận hành. Toàn bộ hệ thống
(Zalo OA + AI) được quy về một gói đầu tư duy nhất, có dòng tiền theo năm,
có chi phí vốn, có rủi ro định lượng bằng phân phối xác suất.

> Toàn bộ số liệu là giả định có căn cứ, dựa trên nguồn công khai. Không có
> số liệu nội bộ nào của Shopee hay Shopee Xpress.

---

## Kết quả

### Kịch bản cơ sở

Với quy mô pilot ~45,900 đơn COD/tháng (0.1% tổng đơn Shopee VN), WACC 10%,
vòng đời 3 năm:

| Chỉ tiêu | Giá trị |
|---|---|
| CF₀ | 680,000,000 VNĐ |
| NPV | **191,937,012 VNĐ** |
| IRR | **25.00%** |
| Payback | **2.07 năm** |

### Monte Carlo (1,000 kịch bản)

Hai biến ngẫu nhiên: mức giảm RTO (Beta) và quy mô đơn COD/tháng (Normal).

| Chỉ tiêu | Giá trị |
|---|---|
| P(NPV > 0) | **70.10%** |
| P(NPV < 0) | 29.90% |
| VaR 95% | **−383,395,638 VNĐ** |
| NPV trung bình | 182,547,623 VNĐ |
| NPV độ lệch chuẩn | 339,163,065 VNĐ |
| **Ngưỡng hòa vốn (mức giảm RTO)** | **28.94%** |
| Xác suất đạt ngưỡng | **71.70%** |

### Kết luận

Ngưỡng hòa vốn là **28.94%**. Benchmark từ các case study trong khu vực
(Dondy, Codrocket — WhatsApp/SMS COD confirmation) ghi nhận mức giảm
30–40%. Xác suất đạt ngưỡng từ mô phỏng là 71.7%, cao hơn ngưỡng quyết
định 50%.

→ **Đầu tư khả thi** với điều kiện: benchmark khu vực giữ được ở mức
30–40%, và quy mô đơn COD không giảm xuống dưới ~30,000 đơn/tháng.

---

## Phương pháp

### Lớp 1 — Capital Budgeting

Bảng dòng tiền 3 năm:

- **CF₀** = 680M (phát triển AI + tích hợp API + đào tạo shipper)
- **Cash Inflow** = Số đơn RTO giảm được × 28,000 VNĐ/đơn (chi phí ship
  chiều đi + phân loại kho — phần thực sự tiết kiệm được)
- **OpEx** = Gói Zalo OA 2.5M/năm + ZNS 300đ/tin × 1 tin/đơn
- **Khấu hao** = CF₀ / 3 năm
- **Chiết khấu** = WACC 10%/năm

Lưu ý quan trọng: đơn không bị hoàn thì **vẫn phải trả phí ship chiều đi**.
Phần tiết kiệm được chỉ là **chi phí chuyển hoàn + chi phí phân loại kho**
(28,000 VNĐ/đơn), không phải toàn bộ 45,000 VNĐ chi phí tổn thất khi đơn
bị hoàn.

### Lớp 2 — Monte Carlo

Hai biến ngẫu nhiên, 1,000 kịch bản:

- **Mức giảm RTO** ~ Beta(α=7.61, β=14.14), mean 35%, neo vào benchmark
  khu vực
- **Quy mô đơn COD/tháng** ~ Normal(μ=45,897, σ=10%μ)

Với mỗi cặp giá trị, dựng bảng dòng tiền và tính NPV. Kết quả dùng để tính
VaR 95%, xác suất lỗ, và break-even.

### Sensitivity analysis

Cả hai biến đều nhân tuyến tính vào cash flow, nên sensitivity một chiều
cho ra biên độ ảnh hưởng giống hệt nhau. Kết luận chuyển sang **rủi ro tương
đối**:

| Biến | Mean | Std | Hệ số biến thiên (CV) |
|---|---|---|---|
| Mức giảm RTO | 0.35 | 0.10 | 28.6% |
| Quy mô đơn COD | 45,897 | 4,590 | 10.0% |

→ Mức giảm RTO có độ bất định cao gấp ~3 lần. Ưu tiên đầu tư vào **giảm bất
định của mức giảm RTO** (pilot nhỏ để đo lường chính xác trước khi scale),
không phải mở rộng quy mô đơn hàng.

---

## Cấu trúc project

Toàn bộ tham số nằm trong file Excel `data/raw/ShopeeXpress_RTO_Model.xlsx`.

---

## Cách chạy

Yêu cầu: Python 3.11+.

```bash
git clone https://github.com/hoanghanghub/shopee-rto-analysis.git
cd shopee-rto-analysis

python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
python main.py