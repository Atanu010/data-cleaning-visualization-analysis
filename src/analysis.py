"""Reusable sales summaries and data-backed business insights."""

from __future__ import annotations

import pandas as pd


def key_metrics(data: pd.DataFrame) -> dict[str, float | int]:
    """Return headline measures for the currently selected orders."""
    if data.empty:
        return {"sales": 0.0, "orders": 0, "average_order": 0.0, "median_order": 0.0}
    return {
        "sales": float(data["sales"].sum()),
        "orders": int(data["order_id"].nunique()),
        "average_order": float(data["sales"].mean()),
        "median_order": float(data["sales"].median()),
    }


def regional_performance(data: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sales, order count, average order, and mix by region."""
    result = data.groupby("region", observed=True).agg(
        sales=("sales", "sum"),
        orders=("order_id", "nunique"),
        average_order=("sales", "mean"),
    )
    if not result.empty:
        result["sales_share"] = result["sales"] / result["sales"].sum()
    return result.sort_values("sales", ascending=False)


def monthly_performance(data: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sales and orders by calendar month."""
    if data.empty:
        return pd.DataFrame(columns=["month", "sales", "orders"])
    monthly = (
        data.assign(month=data["order_date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)
        .agg(sales=("sales", "sum"), orders=("order_id", "nunique"))
    )
    return monthly.sort_values("month")


def outlier_impact(data: pd.DataFrame) -> dict[str, float | int]:
    """Describe flagged sales as a share of the complete selected population."""
    flagged = data.loc[data["is_sales_outlier"]]
    total_sales = float(data["sales"].sum())
    flagged_sales = float(flagged["sales"].sum())
    return {
        "orders": int(len(flagged)),
        "sales": flagged_sales,
        "sales_share": flagged_sales / total_sales if total_sales else 0.0,
        "largest_order": float(flagged["sales"].max()) if not flagged.empty else 0.0,
    }


def business_insights(baseline: pd.DataFrame, complete: pd.DataFrame) -> list[str]:
    """Build concise, qualified findings from baseline and complete populations."""
    if baseline.empty:
        return ["No orders match the selected filters. Widen the selection to review performance."]

    total = float(baseline["sales"].sum())
    regions = regional_performance(baseline)
    products = baseline.groupby("product", observed=True)["sales"].sum().sort_values(ascending=False)
    region, region_row = regions.index[0], regions.iloc[0]
    product = products.index[0]
    product_share = float(products.iloc[0] / total) if total else 0.0
    impact = outlier_impact(complete)

    return [
        f"{region} leads the inlier comparison at ${region_row['sales']:,.2f} across {int(region_row['orders'])} orders ({region_row['sales_share']:.0%} of inlier sales).",
        f"{product} contributes the most inlier sales at ${products.iloc[0]:,.2f} ({product_share:.0%} of the inlier total).",
        f"{impact['orders']} IQR-flagged orders contribute ${impact['sales']:,.2f} ({impact['sales_share']:.1%} of all selected sales); validate these transactions before using headline totals.",
    ]