# Sales Data Cleaning and Visualization Report

## Objective

Demonstrate a reproducible workflow for validating, cleaning, and exploring a deliberately imperfect retail sales dataset.

## Method

The pipeline standardizes region and product labels, parses order dates, converts quantity and unit price to numeric values, and removes duplicate order IDs. Missing numeric values are filled with the column median; missing categorical values use the mode. Rows with invalid dates are excluded because they cannot be placed in time-based analysis. Sales are calculated as quantity multiplied by unit price.

Potential sales outliers are flagged using the 1.5-IQR rule and retained for review. An unusual order can reflect a legitimate large purchase, so it should not be dropped without domain context.

## Outputs

Running `python -m src.visualization` writes the cleaned CSV and five figures: raw-data missingness, sales boxplots, numeric correlation heatmap, sales distribution, and a four-view summary dashboard. The notebook provides the same steps interactively.

## Interpretation Notes

The included CSV is a small synthetic example for demonstrating method, not evidence about a real business. Interpret correlations and apparent regional or product differences cautiously; the sample is not designed for statistical inference.