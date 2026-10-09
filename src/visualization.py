"""Create analysis figures and run the sales-data pipeline."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.analysis import monthly_performance, regional_performance
from src.data_cleaning import clean_sales_data

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "sales_data.csv"
IMAGE_DIR = ROOT / "images"


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_missing_values(raw: pd.DataFrame, output_dir: Path = IMAGE_DIR) -> Path:
    counts = raw.isna().sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(x=counts.index, y=counts.values, color="#3a7d78", ax=ax)
    ax.set(title="Missing Values by Column", xlabel="Column", ylabel="Missing rows")
    ax.tick_params(axis="x", rotation=25)
    path = output_dir / "missing_values.png"
    _save(fig, path)
    return path


def plot_outliers(data: pd.DataFrame, output_dir: Path = IMAGE_DIR) -> Path:
    fig, ax = plt.subplots(figsize=(7, 4))
    baseline = data.loc[~data["is_sales_outlier"]]
    regions = sorted(data["region"].dropna().unique())
    sns.boxplot(data=baseline, x="sales", y="region", order=regions, showfliers=False, color="#83b6a5", ax=ax)
    positions = {region: index for index, region in enumerate(regions)}
    flagged = data.loc[data["is_sales_outlier"]]
    if not flagged.empty:
        ax.scatter(
            flagged["sales"],
            flagged["region"].map(positions),
            marker="D",
            color="#c75b45",
            label="IQR-flagged order",
            zorder=5,
        )
        ax.legend(frameon=False)
    ax.set_xscale("log")
    ax.set(title="Typical Order Values and Flagged Transactions", xlabel="Sales (log scale)", ylabel="Region")
    path = output_dir / "outliers.png"
    _save(fig, path)
    return path


def plot_correlation_heatmap(data: pd.DataFrame, output_dir: Path = IMAGE_DIR) -> Path:
    numeric = data[["quantity", "unit_price", "sales"]]
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(numeric.corr(), annot=True, cmap="YlGnBu", fmt=".2f", ax=ax)
    ax.set_title("Order Metrics Correlation")
    path = output_dir / "heatmap.png"
    _save(fig, path)
    return path


def plot_sales_distribution(data: pd.DataFrame, output_dir: Path = IMAGE_DIR) -> Path:
    baseline = data.loc[~data["is_sales_outlier"]]
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(data=baseline, x="sales", hue="region", bins=12, element="step", ax=ax)
    ax.set(
        title=f"Order Sales Distribution (inlier orders; {int(data['is_sales_outlier'].sum())} flagged separately)",
        xlabel="Sales",
        ylabel="Order count",
    )
    path = output_dir / "sales_distribution.png"
    _save(fig, path)
    return path


def plot_dashboard(data: pd.DataFrame, output_dir: Path = IMAGE_DIR) -> Path:
    baseline = data.loc[~data["is_sales_outlier"]]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    region_sales = regional_performance(baseline)["sales"].sort_values()
    axes[0, 0].barh(region_sales.index, region_sales.values, color="#3a7d78")
    axes[0, 0].set(title="Sales by Region", xlabel="Sales")
    sns.histplot(data=baseline, x="sales", bins=12, color="#e7a44a", ax=axes[0, 1])
    axes[0, 1].set(title="Order Value Distribution (IQR inliers)", xlabel="Sales")
    product_sales = baseline.groupby("product", observed=True)["sales"].sum().sort_values()
    axes[1, 0].bar(product_sales.index, product_sales.values, color="#507aa5")
    axes[1, 0].set(title="Sales by Product", ylabel="Sales")
    monthly = monthly_performance(baseline)
    axes[1, 1].plot(monthly["month"], monthly["sales"], marker="o", color="#bf5b45")
    axes[1, 1].set(title="Monthly Sales (IQR inliers)", ylabel="Sales")
    axes[1, 1].tick_params(axis="x", rotation=30)
    fig.suptitle("Sales Overview | IQR-Flagged Orders Excluded from Comparisons", y=1.02)
    path = output_dir / "dashboard.png"
    _save(fig, path)
    return path


def run_analysis(data_path: Path = DATA_PATH, output_dir: Path = IMAGE_DIR) -> pd.DataFrame:
    """Clean the input, save its cleaned form and all five project figures."""
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(data_path)
    plot_missing_values(raw, output_dir)
    cleaned = clean_sales_data(raw)
    cleaned.to_csv(data_path.with_name("cleaned_sales_data.csv"), index=False)
    plot_outliers(cleaned, output_dir)
    plot_correlation_heatmap(cleaned, output_dir)
    plot_sales_distribution(cleaned, output_dir)
    plot_dashboard(cleaned, output_dir)
    return cleaned


if __name__ == "__main__":
    result = run_analysis()
    print(f"Cleaned {len(result)} orders; flagged {int(result['is_sales_outlier'].sum())} sales outliers.")
    print(f"Figures saved to {IMAGE_DIR}")