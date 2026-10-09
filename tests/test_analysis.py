from pathlib import Path

import pandas as pd

from src.analysis import business_insights, key_metrics, monthly_performance, outlier_impact, regional_performance
from src.data_cleaning import cleaning_audit, clean_sales_data, validate_sales_data


def sample_raw_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": [1, 2, 3, 1, 4],
            "order_date": ["2025-01-01", "2025-01-12", "2025-02-10", "2025-01-01", "bad-date"],
            "region": [" north ", "South", "North", "North", "West"],
            "product": ["A", "B", "A", "A", "B"],
            "quantity": [2, None, 3, 2, 1],
            "unit_price": [10, 20, 10, 10, 20],
        }
    )


def test_cleaning_deduplicates_imputes_and_excludes_invalid_dates() -> None:
    raw = sample_raw_data()
    clean = clean_sales_data(raw)

    assert len(clean) == 3
    assert clean["order_id"].is_unique
    assert clean["quantity"].notna().all()
    assert clean["region"].tolist() == ["North", "South", "North"]
    assert clean["sales"].tolist() == [20, 40, 30]
    assert pd.api.types.is_integer_dtype(clean["quantity"])
    assert clean["is_sales_outlier"].dtype == bool
    validate_sales_data(clean)


def test_cleaning_audit_explains_row_changes() -> None:
    raw = sample_raw_data()
    clean = clean_sales_data(raw)
    audit = cleaning_audit(raw, clean)

    assert audit["raw_rows"] == 5
    assert audit["clean_rows"] == 3
    assert audit["duplicate_order_ids_removed"] == 1
    assert audit["invalid_dates_removed"] == 1
    assert audit["imputed"]["quantity"] == 1


def test_summaries_and_insights_use_aggregated_data() -> None:
    clean = clean_sales_data(sample_raw_data())
    baseline = clean.loc[~clean["is_sales_outlier"]]

    assert key_metrics(baseline)["orders"] == 3
    assert regional_performance(baseline).iloc[0]["sales"] == 50
    assert monthly_performance(baseline)["orders"].sum() == 3
    assert outlier_impact(clean)["orders"] == 0
    assert len(business_insights(baseline, clean)) == 3


def test_documented_sample_findings_are_reproducible() -> None:
    root = Path(__file__).resolve().parents[1]
    raw = pd.read_csv(root / "data" / "sales_data.csv")
    clean = clean_sales_data(raw)
    baseline = clean.loc[~clean["is_sales_outlier"]]
    impact = outlier_impact(clean)

    assert len(raw) == 50
    assert len(clean) == 49
    assert impact["orders"] == 2
    assert impact["sales"] == 3340
    assert impact["largest_order"] == 3120
    assert regional_performance(baseline).index[0] == "East"
    assert baseline.groupby("product")["sales"].sum().idxmax() == "Widget C"