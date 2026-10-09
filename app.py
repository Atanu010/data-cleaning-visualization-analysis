"""Interactive portfolio dashboard for the synthetic sales sample."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analysis import business_insights, key_metrics, monthly_performance, outlier_impact, regional_performance
from src.data_cleaning import cleaning_audit, clean_sales_data

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "sales_data.csv"

st.set_page_config(page_title="Sales Performance | Analyst Portfolio", page_icon="▦", layout="wide")
st.markdown(
    """
    <style>
      .block-container {max-width: 1320px; padding-top: 2rem; padding-bottom: 3rem;}
      [data-testid="stMetric"] {background: #f4f7f5; border: 1px solid #dce6e0; padding: 14px 16px; border-radius: 6px;}
      [data-testid="stSidebar"] {background: #f5f7f6;}
      .portfolio-note {padding: 12px 16px; background: #fff6e8; border-left: 4px solid #d8963f; margin: 1rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Cleaning sample data…")
def load_sales(path: str, modified_time: float) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    raw = pd.read_csv(path)
    cleaned = clean_sales_data(raw)
    return raw, cleaned, cleaning_audit(raw, cleaned)


raw_data, sales_data, audit = load_sales(str(DATA_PATH), DATA_PATH.stat().st_mtime)

st.title("Sales Performance Explorer")
st.caption("A reproducible data-cleaning and exploratory analysis case study | Synthetic retail orders, Jan–Jun 2025")
st.markdown(
    '<div class="portfolio-note"><strong>Interpretation guardrail:</strong> This is a synthetic portfolio dataset. '
    "Findings demonstrate analytical workflow; they are not evidence of real customer demand.</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Analysis filters")
    available_regions = sorted(sales_data["region"].unique().tolist())
    available_products = sorted(sales_data["product"].unique().tolist())
    selected_regions = st.multiselect("Region", available_regions, default=available_regions)
    selected_products = st.multiselect("Product", available_products, default=available_products)
    min_date = sales_data["order_date"].min().date()
    max_date = sales_data["order_date"].max().date()
    date_range = st.date_input("Order date", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    include_outliers = st.checkbox(
        "Include IQR-flagged orders in KPIs and charts",
        value=False,
        help="Off by default so a small number of unusual transactions do not dominate comparisons.",
    )

if len(date_range) != 2:
    st.info("Select a start and end date to see the analysis.")
    st.stop()

selected = sales_data.loc[
    sales_data["region"].isin(selected_regions)
    & sales_data["product"].isin(selected_products)
    & sales_data["order_date"].dt.date.between(date_range[0], date_range[1])
].copy()

if selected.empty:
    st.info("No orders match the current filters. Expand the date range or select more categories.")
    st.stop()

baseline = selected.loc[~selected["is_sales_outlier"]].copy()
analysis_data = selected if include_outliers else baseline
metrics = key_metrics(analysis_data)
impact = outlier_impact(selected)

metric_columns = st.columns(4)
metric_columns[0].metric("Sales in view", f"${metrics['sales']:,.2f}")
metric_columns[1].metric("Orders in view", f"{metrics['orders']:,}")
metric_columns[2].metric("Average order", f"${metrics['average_order']:,.2f}")
metric_columns[3].metric("Median order", f"${metrics['median_order']:,.2f}")
st.caption(
    f"KPIs and charts {'include' if include_outliers else 'exclude'} IQR-flagged orders. "
    f"Current selection contains {impact['orders']} flagged orders (${impact['sales']:,.2f}; {impact['sales_share']:.1%} of selected sales)."
)

performance_tab, quality_tab, detail_tab = st.tabs(["Performance", "Data quality", "Order detail"])

with performance_tab:
    left, right = st.columns(2)
    with left:
        monthly = monthly_performance(analysis_data)
        monthly_figure = px.line(monthly, x="month", y="sales", markers=True, title="Monthly sales")
        monthly_figure.update_layout(xaxis_title=None, yaxis_title="Sales ($)", hovermode="x unified")
        st.plotly_chart(monthly_figure, width="stretch")
    with right:
        regions = regional_performance(analysis_data).reset_index()
        region_figure = px.bar(regions.sort_values("sales"), x="sales", y="region", orientation="h", text_auto="$.2s", title="Sales by region")
        region_figure.update_layout(xaxis_title="Sales ($)", yaxis_title=None)
        st.plotly_chart(region_figure, width="stretch")

    left, right = st.columns(2)
    with left:
        product_sales = analysis_data.groupby("product", as_index=False, observed=True)["sales"].sum().sort_values("sales")
        product_figure = px.bar(product_sales, x="sales", y="product", orientation="h", text_auto="$.2s", title="Sales by product")
        product_figure.update_layout(xaxis_title="Sales ($)", yaxis_title=None)
        st.plotly_chart(product_figure, width="stretch")
    with right:
        distribution = px.histogram(analysis_data, x="sales", color="region", marginal="box", nbins=14, title="Order value distribution")
        distribution.update_layout(xaxis_title="Order value ($)", yaxis_title="Orders")
        st.plotly_chart(distribution, width="stretch")

    st.subheader("What stands out")
    st.caption("Comparative insights use IQR inliers; flagged orders are reported separately for review.")
    for insight in business_insights(baseline, selected):
        st.markdown(f"- {insight}")

with quality_tab:
    st.subheader("Cleaning audit")
    audit_columns = st.columns(4)
    audit_columns[0].metric("Raw rows", audit["raw_rows"])
    audit_columns[1].metric("Clean orders", audit["clean_rows"])
    audit_columns[2].metric("Duplicate IDs removed", audit["duplicate_order_ids_removed"])
    audit_columns[3].metric("IQR orders flagged", audit["outliers_flagged"])
    st.markdown("**Missing values before cleaning**")
    missing_table = pd.DataFrame(
        {"Missing or blank values": audit["missing_before"], "Values imputed": audit["imputed"]}
    ).rename_axis("Field")
    st.dataframe(missing_table, width="stretch")
    st.markdown(
        "Rows without an order ID or parseable date are excluded. Numeric gaps use the median; categorical gaps use the mode. "
        "Duplicate IDs keep the first occurrence. Outliers remain in the cleaned data and are only flagged."
    )

with detail_tab:
    st.subheader("Flagged transactions")
    flagged = selected.loc[selected["is_sales_outlier"]].sort_values("sales", ascending=False)
    if flagged.empty:
        st.success("No IQR-flagged orders in this selection.")
    else:
        st.dataframe(flagged, width="stretch", hide_index=True)
    st.download_button(
        "Download filtered orders as CSV",
        data=selected.to_csv(index=False).encode("utf-8"),
        file_name="filtered_sales_analysis.csv",
        mime="text/csv",
    )