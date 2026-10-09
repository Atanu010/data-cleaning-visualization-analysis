"""Cleaning and validation helpers for the sales dataset."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = ["order_id", "order_date", "region", "product", "quantity", "unit_price"]


def missing_value_summary(data: pd.DataFrame) -> pd.Series:
    """Return nonzero missing-value counts by column."""
    return data.isna().sum().loc[lambda counts: counts.gt(0)].sort_values(ascending=False)


def clean_sales_data(data: pd.DataFrame) -> pd.DataFrame:
    """Standardize sales fields, remove duplicate orders, and impute missing values."""
    missing_columns = set(REQUIRED_COLUMNS) - set(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing_columns))}")

    cleaned = data.loc[:, REQUIRED_COLUMNS].copy()
    cleaned = cleaned.drop_duplicates(subset="order_id", keep="first")
    cleaned["order_date"] = pd.to_datetime(cleaned["order_date"], errors="coerce")
    cleaned["region"] = cleaned["region"].astype("string").str.strip().str.title()
    cleaned["product"] = cleaned["product"].astype("string").str.strip()

    for column in ("quantity", "unit_price"):
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
        median = cleaned[column].median()
        if pd.isna(median):
            raise ValueError(f"Cannot impute {column}: column contains no valid numeric values")
        cleaned[column] = cleaned[column].fillna(median)

    for column in ("region", "product"):
        mode = cleaned[column].mode(dropna=True)
        if mode.empty:
            raise ValueError(f"Cannot impute {column}: column contains no valid values")
        cleaned[column] = cleaned[column].fillna(mode.iloc[0])

    cleaned = cleaned.dropna(subset=["order_date"])
    cleaned["sales"] = cleaned["quantity"] * cleaned["unit_price"]
    cleaned["is_sales_outlier"] = flag_iqr_outliers(cleaned["sales"])
    return cleaned.reset_index(drop=True)


def flag_iqr_outliers(values: pd.Series) -> pd.Series:
    """Flag values outside the 1.5-IQR fences without removing observations."""
    first_quartile, third_quartile = values.quantile([0.25, 0.75])
    spread = third_quartile - first_quartile
    return values.lt(first_quartile - 1.5 * spread) | values.gt(third_quartile + 1.5 * spread)