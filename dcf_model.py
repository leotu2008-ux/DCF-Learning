"""
A from-scratch DCF (Discounted Cash Flow) valuation model.

The mental model, in order:
  1. Project free cash flow (FCF) for the next N years.
  2. Discount each year's FCF back to today's dollars using the
     discount rate (WACC).
  3. Estimate a "terminal value" — the value of all cash flows
     beyond the projection window — and discount that back too.
  4. Sum everything to get Enterprise Value (the value of the
     whole business, before debt/cash).
  5. Adjust for net debt to get Equity Value (what shareholders own).
  6. Divide by shares outstanding to get a per-share price.

Edit the numbers in `main()` to value a real company. Everything
else is just the math, kept in small, readable functions.
"""

from dataclasses import dataclass, field


@dataclass
class DCFInputs:
    # --- Starting financials (most recent actual year) ---
    revenue: float                 # last year's revenue ($)
    ebit_margin: float             # EBIT / revenue, e.g. 0.20 = 20%
    tax_rate: float                # e.g. 0.25 = 25%
    d_and_a_pct_revenue: float     # depreciation & amortization, % of revenue
    capex_pct_revenue: float       # capital expenditures, % of revenue
    nwc_pct_revenue: float         # net working capital, % of revenue
                                    # (used to find the *change* in NWC each year)

    # --- Growth assumptions ---
    revenue_growth_rates: list     # one growth rate per projection year, e.g.
                                    # [0.10, 0.09, 0.08, 0.07, 0.06] for 5 years

    # --- Discounting ---
    discount_rate: float           # WACC, e.g. 0.09 = 9%
    terminal_growth_rate: float    # perpetuity growth rate after year N, e.g. 0.025

    # --- Bridge from Enterprise Value to per-share price ---
    net_debt: float                # total debt minus cash
    shares_outstanding: float


@dataclass
class YearProjection:
    year: int
    revenue: float
    ebit: float
    nopat: float                   # EBIT after tax (Net Operating Profit After Tax)
    d_and_a: float
    capex: float
    change_in_nwc: float
    free_cash_flow: float
    discount_factor: float
    present_value: float


def project_free_cash_flows(inputs: DCFInputs) -> list:
    """
    Build the year-by-year FCF forecast.

    Free Cash Flow here is "unlevered FCF" (cash flow to the whole
    business, before financing decisions), computed as:

        NOPAT (after-tax operating profit)
        + D&A            (add back — it's a non-cash expense)
        - CapEx          (cash actually spent on equipment/facilities)
        - Change in NWC  (cash tied up in inventory/receivables, etc.)
        = Free Cash Flow

    This is the standard bridge from "accounting profit" to "actual
    spendable cash," which is the whole point of a DCF.
    """
    projections = []
    prior_revenue = inputs.revenue
    prior_nwc = inputs.revenue * inputs.nwc_pct_revenue

    for i, growth_rate in enumerate(inputs.revenue_growth_rates, start=1):
        revenue = prior_revenue * (1 + growth_rate)
        ebit = revenue * inputs.ebit_margin
        nopat = ebit * (1 - inputs.tax_rate)
        d_and_a = revenue * inputs.d_and_a_pct_revenue
        capex = revenue * inputs.capex_pct_revenue

        nwc = revenue * inputs.nwc_pct_revenue
        change_in_nwc = nwc - prior_nwc

        fcf = nopat + d_and_a - capex - change_in_nwc

        discount_factor = 1 / (1 + inputs.discount_rate) ** i
        present_value = fcf * discount_factor

        projections.append(YearProjection(
            year=i,
            revenue=revenue,
            ebit=ebit,
            nopat=nopat,
            d_and_a=d_and_a,
            capex=capex,
            change_in_nwc=change_in_nwc,
            free_cash_flow=fcf,
            discount_factor=discount_factor,
            present_value=present_value,
        ))

        prior_revenue = revenue
        prior_nwc = nwc

    return projections


def terminal_value(inputs: DCFInputs, projections: list) -> tuple:
    """
    Everything after the last projected year is compressed into one
    number using the Gordon Growth (perpetuity) formula:

        TV (at end of final year) = FCF_final * (1 + g) / (r - g)

    where g is a modest, sustainable long-run growth rate (roughly
    GDP growth, not the high growth used in early years) and r is
    the discount rate. This TV is a lump sum sitting at the end of
    year N, so it still needs to be discounted back to today.

    Returns (undiscounted_terminal_value, present_value_of_terminal_value).
    """
    final_year_fcf = projections[-1].free_cash_flow
    g = inputs.terminal_growth_rate
    r = inputs.discount_rate

    if r <= g:
        raise ValueError("Discount rate must exceed terminal growth rate.")

    tv = final_year_fcf * (1 + g) / (r - g)
    pv_of_tv = tv * projections[-1].discount_factor

    return tv, pv_of_tv


def run_dcf(inputs: DCFInputs) -> dict:
    """Runs the full model and returns every intermediate + final result."""
    projections = project_free_cash_flows(inputs)

    pv_of_explicit_fcf = sum(p.present_value for p in projections)
    tv, pv_of_tv = terminal_value(inputs, projections)

    enterprise_value = pv_of_explicit_fcf + pv_of_tv
    equity_value = enterprise_value - inputs.net_debt
    value_per_share = equity_value / inputs.shares_outstanding

    return {
        "projections": projections,
        "pv_of_explicit_fcf": pv_of_explicit_fcf,
        "terminal_value": tv,
        "pv_of_terminal_value": pv_of_tv,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "value_per_share": value_per_share,
    }


def print_report(inputs: DCFInputs, result: dict) -> None:
    def money(x):
        return f"${x:,.1f}"

    print("=" * 72)
    print("YEAR-BY-YEAR FREE CASH FLOW PROJECTION")
    print("=" * 72)
    header = f"{'Yr':>3} {'Revenue':>12} {'EBIT':>12} {'NOPAT':>12} {'FCF':>12} {'PV of FCF':>12}"
    print(header)
    for p in result["projections"]:
        print(f"{p.year:>3} {money(p.revenue):>12} {money(p.ebit):>12} "
              f"{money(p.nopat):>12} {money(p.free_cash_flow):>12} "
              f"{money(p.present_value):>12}")

    print()
    print("=" * 72)
    print("VALUATION SUMMARY")
    print("=" * 72)
    print(f"{'PV of explicit-period FCF:':<38}{money(result['pv_of_explicit_fcf']):>15}")
    print(f"{'Terminal value (undiscounted):':<38}{money(result['terminal_value']):>15}")
    print(f"{'PV of terminal value:':<38}{money(result['pv_of_terminal_value']):>15}")
    print("-" * 72)
    print(f"{'Enterprise Value:':<38}{money(result['enterprise_value']):>15}")
    print(f"{'Less: Net Debt':<38}{money(-inputs.net_debt):>15}")
    print(f"{'Equity Value:':<38}{money(result['equity_value']):>15}")
    print("-" * 72)
    print(f"{'Shares Outstanding:':<38}{inputs.shares_outstanding:>15,.1f}")
    print(f"{'Value Per Share:':<38}{money(result['value_per_share']):>15}")
    print("=" * 72)

    tv_pct = result["pv_of_terminal_value"] / result["enterprise_value"] * 100
    print(f"\nNote: {tv_pct:.0f}% of Enterprise Value comes from the terminal "
          f"value.\nThat's normal for a DCF, but it also means the model is "
          f"very sensitive\nto the terminal growth rate and discount rate — "
          f"worth stress-testing both.")


def main():
    # Example: a mid-size, moderately growing company.
    # Replace these with a real company's numbers to value it.
    inputs = DCFInputs(
        revenue=1_000.0,               # $1,000M last year
        ebit_margin=0.20,              # 20% operating margin
        tax_rate=0.25,
        d_and_a_pct_revenue=0.04,
        capex_pct_revenue=0.05,
        nwc_pct_revenue=0.10,
        revenue_growth_rates=[0.10, 0.09, 0.08, 0.07, 0.06],  # 5-year forecast
        discount_rate=0.09,            # 9% WACC
        terminal_growth_rate=0.025,    # 2.5% long-run growth
        net_debt=500.0,                # $500M net debt
        shares_outstanding=100.0,      # 100M shares
    )

    result = run_dcf(inputs)
    print_report(inputs, result)


if __name__ == "__main__":
    main()
