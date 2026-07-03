# DCF-Learning

A from-scratch Discounted Cash Flow (DCF) valuation model, built to learn
how DCF valuation actually works — no spreadsheet magic, just readable
Python you can trace line by line.

## What's here

`dcf_model.py` — a single-file, dependency-free DCF model that:

1. Projects unlevered free cash flow (FCF) for a 5-year forecast window
   from revenue growth, operating margin, tax rate, D&A, CapEx, and
   working-capital assumptions.
2. Discounts each year's FCF back to present value using a discount rate
   (WACC).
3. Estimates a terminal value for everything beyond the forecast window
   (Gordon Growth / perpetuity method) and discounts that back too.
4. Sums it all into Enterprise Value, bridges to Equity Value by
   subtracting net debt, and divides by shares outstanding for a
   per-share estimate.

The included example values Apple (AAPL) using real FY2025 10-K figures
(revenue, margin, tax rate, D&A/CapEx, net cash, share count), with the
growth rate and discount rate clearly marked as estimates rather than
disclosed numbers.

## Requirements

Python 3 — no external packages.

## Usage

```
python3 dcf_model.py
```

This prints a year-by-year FCF table followed by a valuation summary
(Enterprise Value, Equity Value, and value per share).

To value a different company or test different assumptions, edit the
`DCFInputs(...)` block inside `main()` in `dcf_model.py` — revenue,
margin, tax rate, growth rates, discount rate, terminal growth rate, net
debt, and shares outstanding — then re-run the script.

## How to read the code

Work through `dcf_model.py` top to bottom:

- `DCFInputs` — every assumption the model takes in, in one place
- `project_free_cash_flows` — builds the year-by-year FCF forecast
- `terminal_value` — values everything past the forecast window
- `run_dcf` — runs the full model and returns all intermediate results
- `print_report` — formats the output

Each function has a short comment explaining the *why* behind the math,
not just the what.
