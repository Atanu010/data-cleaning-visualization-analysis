"""Cleaning and validation helpers for the sales dataset."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = ["order_id", "order_date", "region", "product", "quantity", "unit_price"]
OUTPUT_COLUMNS = REQUIRED_COLUMNS + ["sales", "is_sales_outlier"]


def missing_value_summary(data: pd.DataFrame) -> pd.Series:
    """Return nonzero missing-value counts by column."""
    return data.isna().sum().loc[lambda counts: counts.gt(0)].sort_values(ascending=False)


def clean_sales_data(data: pd.DataFrame) -> pd.DataFrame:
    """Standardize sales fields, deduplicate orders, and impute missing values.

    Rows without an order ID or parseable order date are excluded. Duplicate IDs
    keep their first occurrence; use ``cleaning_audit`` to inspect these choices.
    """
    missing_columns = set(REQUIRED_COLUMNS) - set(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing_columns))}")

    cleaned = data.loc[:, REQUIRED_COLUMNS].copy()
    cleaned["region"] = cleaned["region"].replace(r"^\s*$", pd.NA, regex=True)
    cleaned["product"] = cleaned["product"].replace(r"^\s*$", pd.NA, regex=True)
    cleaned = cleaned.dropna(subset=["order_id"])
    cleaned = cleaned.drop_duplicates(subset="order_id", keep="first")
    cleaned["order_date"] = pd.to_datetime(cleaned["order_date"], errors="coerce")
    cleaned = cleaned.dropna(subset=["order_date"])
    cleaned["region"] = cleaned["region"].astype("string").str.strip().str.title()
    cleaned["product"] = cleaned["product"].astype("string").str.strip()

    for column in ("quantity", "unit_price"):
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
        median = cleaned[column].median()
        if pd.isna(median):
            raise ValueError(f"Cannot impute {column}: column contains no valid numeric values")
        cleaned[column] = cleaned[column].fillna(median)
        if column == "quantity":
            cleaned[column] = cleaned[column].round().astype("int64")

    for column in ("region", "product"):
        mode = cleaned[column].mode(dropna=True)
        if mode.empty:
            raise ValueError(f"Cannot impute {column}: column contains no valid values")
        cleaned[column] = cleaned[column].fillna(mode.iloc[0])

    cleaned["sales"] = cleaned["quantity"] * cleaned["unit_price"]
    cleaned["is_sales_outlier"] = flag_iqr_outliers(cleaned["sales"])
    cleaned = cleaned.reset_index(drop=True)
    validate_sales_data(cleaned)
    return cleaned


def flag_iqr_outliers(values: pd.Series) -> pd.Series:
    """Flag values outside the 1.5-IQR fences without removing observations."""
    first_quartile, third_quartile = values.quantile([0.25, 0.75])
    spread = third_quartile - first_quartile
    return values.lt(first_quartile - 1.5 * spread) | values.gt(third_quartile + 1.5 * spread)


def validate_sales_data(data: pd.DataFrame) -> None:
    """Raise a clear error when cleaned sales data violates the analysis contract."""
    missing_columns = set(OUTPUT_COLUMNS) - set(data.columns)
    if missing_columns:
        raise ValueError(f"Missing output columns: {', '.join(sorted(missing_columns))}")
    if data[OUTPUT_COLUMNS].isna().any().any():
        raise ValueError("Cleaned sales data contains missing required values")
    if data["order_id"].duplicated().any():
        raise ValueError("Cleaned sales data contains duplicate order IDs")
    if data["quantity"].le(0).any() or data["unit_price"].le(0).any():
        raise ValueError("Quantity and unit price must be positive")


def cleaning_audit(raw: pd.DataFrame, cleaned: pd.DataFrame) -> dict[str, object]:
    """Summarize row handling and missingness for transparent review."""
    raw_rows = len(raw)
    missing = {column: int(raw[column].isna().sum()) for column in REQUIRED_COLUMNS}
    for column in ("region", "product"):
        missing[column] += int(raw[column].astype("string").str.strip().eq("").sum())

    numeric_imputed = {
        column: int(pd.to_numeric(raw[column], errors="coerce").isna().sum())
        for column in ("quantity", "unit_price")
    }
    categorical_imputed = {
        column: int(raw[column].isna().sum() + raw[column].astype("string").str.strip().eq("").sum())
        for column in ("region", "product")
    }
    return {
        "raw_rows": raw_rows,
        "clean_rows": len(cleaned),
        "duplicate_order_ids_removed": int(raw["order_id"].duplicated().sum()),
        "missing_order_ids_removed": int(raw["order_id"].isna().sum()),
        "invalid_dates_removed": int(pd.to_datetime(raw["order_date"], errors="coerce").isna().sum()),
        "missing_before": missing,
        "imputed": numeric_imputed | categorical_imputed,
        "outliers_flagged": int(cleaned["is_sales_outlier"].sum()),
    }