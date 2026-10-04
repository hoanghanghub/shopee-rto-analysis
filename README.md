# Shopee Xpress RTO Reduction — Capital Budgeting & Monte Carlo

A cash-flow model that evaluates whether an automated order-confirmation system
(Zalo OA + AI delivery-time suggestions) is worth building at Shopee Xpress
Vietnam. The goal is a measurable reduction in Return-to-Origin (RTO) — the
single largest hidden cost in Vietnam's e-commerce logistics.

## Why this matters

Every returned COD order costs money twice: the outbound shipping fee (already
paid, never recovered) plus the labor to reclassify the parcel at the warehouse.
At scale, this eats into margin faster than most operational metrics suggest.

This model treats the Zalo OA + AI system as a single capital investment with
a 3-year cash flow, a cost of capital, and a probability distribution over
outcomes — not as an operations project. The question isn't "does the system
work?", it's "what reduction in RTO makes the investment break even, and how
likely is that?"

> All numbers are reasoned estimates from public sources. No internal Shopee
> or Shopee Xpress data is used.

---

## Results

### Base case

Pilot scope ~45,900 COD orders/month (0.1% of Shopee VN total), WACC 10%,
3-year horizon:

| Metric | Value |
|---|---|
| Initial investment (CF₀) | 680,000,000 VND |
| NPV | **191,937,012 VND** |
| IRR | **25.00%** |
| Payback | **2.07 years** |

### Monte Carlo (1,000 scenarios)

Two random variables: RTO reduction rate (Beta) and monthly COD order volume
(Normal).

| Metric | Value |
|---|---|
| P(NPV > 0) | **70.10%** |
| P(NPV < 0) | 29.90% |
| VaR 95% | **−383,395,638 VND** |
| Mean NPV | 182,547,623 VND |
| Std NPV | 339,163,065 VND |
| **Break-even RTO reduction** | **28.94%** |
| Probability of hitting break-even | **71.70%** |

### Takeaway

Break-even sits at a **28.94% reduction in RTO**. Published case studies from
the region (Dondy, Codrocket — WhatsApp/SMS COD confirmation) report 30–40%
reductions. Simulation puts the probability of clearing break-even at 71.7%,
above the 50% decision threshold.

→ **Investment is justified** if two conditions hold: regional benchmarks stay
in the 30–40% range, and monthly COD volume does not drop below ~30,000 orders.

---

## Method

### Layer 1 — Capital Budgeting

Three-year cash flow:

- **CF₀** = 680M VND (AI development + API integration + shipper training)
- **Cash inflow** = prevented RTO orders × 28,000 VND/order. This is the
  truly avoided cost — outbound shipping is still paid on every delivered
  order, so only the return shipping + warehouse reclassification drop out.
- **OpEx** = Zalo OA package (2.5M VND/year) + ZNS messages at 300 VND × 1
  message/order
- **Depreciation** = CF₀ / 3 years, straight-line
- **Discount rate** = WACC 10%

### Layer 2 — Monte Carlo

1,000 scenarios, two random variables:

- **RTO reduction** ~ Beta(α=7.61, β=14.14), mean 35%, anchored to regional
  benchmarks
- **Monthly COD volume** ~ Normal(μ=45,897, σ=10%μ)

Each scenario produces a full cash flow and NPV. The NPV distribution feeds
VaR 95%, loss probability, and break-even estimation.

### Sensitivity

Both variables enter the cash flow linearly, so one-way sensitivity gives
identical impact ranges for each. The meaningful comparison is **relative
uncertainty**:

| Variable | Mean | Std | Coefficient of variation |
|---|---|---|---|
| RTO reduction | 0.35 | 0.10 | 28.6% |
| Monthly COD volume | 45,897 | 4,590 | 10.0% |

RTO reduction is roughly 3× more uncertain. The recommendation that follows:
**invest first in reducing uncertainty around the RTO reduction estimate**
(run a small pilot to measure it precisely before scaling), not in expanding
order volume.

---

## Project structure

Every parameter lives in the Excel file. No constants are hard-coded in Python —
change the Excel, rerun `python main.py`, and every result updates.

---

## How to run

Requires Python 3.11+.

```bash
git clone https://github.com/hoanghanghub/shopee-rto-analysis.git
cd shopee-rto-analysis

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python main.py