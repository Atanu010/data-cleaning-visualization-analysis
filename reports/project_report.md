# Sales Performance Analysis

## Executive Summary

This project demonstrates a reproducible workflow for cleaning and exploring a deliberately imperfect synthetic retail-order dataset. The source contains 50 rows; after keeping the first instance of a duplicate order ID and filling two missing quantities, the cleaned table contains 49 orders. Two orders are flagged by the 1.5-IQR rule and retained for review.

The complete cleaned sample totals **$7,618**. The two flagged transactions total **$3,340** (43.8% of sales), so including them changes the apparent performance profile materially. For comparisons that exclude flagged transactions, the East region leads with **$1,233** (28.8% of inlier sales), while Widget C leads product sales with **$1,797** (42.0%). These are sample descriptions only, not findings about real customers or a market.

## Data and Preparation

The six-column source file covers January to June 2025 and includes order ID, date, region, product, quantity, and unit price. The cleaning function validates required fields; normalizes category text; removes rows without order IDs; keeps the first occurrence of a duplicate order ID; parses dates and excludes invalid dates before computing imputation values; imputes numeric gaps with medians and category gaps with modes; rounds quantity values to whole units; calculates sales; and adds a boolean IQR review flag.

The cleaning audit reports raw and clean row counts, removed duplicate IDs, invalid rows, missing values, imputations, and outlier count. This makes exclusions and assumptions inspectable rather than hiding them in a notebook cell.

## Descriptive Findings

| View | Result on this sample |
| --- | --- |
| Data quality | 50 raw rows, 49 unique cleaned orders, 1 duplicate ID removed, 2 quantities imputed |
| Outlier sensitivity | 2 flagged orders account for $3,340 (43.8%) of cleaned sales |
| Regional baseline | East leads inlier sales at $1,233 (28.8% of the inlier total) |
| Product baseline | Widget C leads inlier sales at $1,797 (42.0% of the inlier total) |

The largest flagged transaction is order `1049` at $3,120. The second flagged order is order `1014` at $220. Both remain in the cleaned output. The dashboard defaults to inlier comparisons, reports flagged-order impact alongside them, and allows users to include flagged records to compare the result.

## Reviewer Interpretation

The key analytical lesson is sensitivity: a small number of valid-but-unusual transactions can dominate aggregates. A reviewer should ask whether the bulk order is an error, a wholesale purchase, or a genuine one-off before deciding how revenue should be reported. Presenting both full and inlier views is more defensible than silently deleting records or presenting one total without qualification.

No causal conclusions, forecasts, or real-world recommendations are supported by this constructed dataset. The region and product patterns are included to exercise aggregation and filtering, not to represent a real commercial opportunity.

## Reproduction

- Interactive dashboard: `python -m streamlit run app.py`
- Static outputs and cleaned CSV: `python -m src.visualization`
- Automated checks: `python -m pytest -q`
- Interactive walkthrough: `notebooks/data_cleaning_analysis.ipynb`

All displayed summary metrics are computed from the cleaned CSV by the shared functions in `src/analysis.py`; the same preparation rules are used by the notebook and dashboard.
