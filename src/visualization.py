"""Create analysis figures and run the sales-data pipeline."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.data_cleaning import clean_sales_data

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "sales_data.csv"
IMAGE_DIR = ROOT / "images"


def _save(fig: plt.Figure, path: Path) -> None:
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
    sns.boxplot(data=data, x="sales", y="region", color="#e7a44a", ax=ax)
    ax.set(title="Sales by Region: IQR Outlier Review", xlabel="Sales", ylabel="Region")
    path = output_dir / "outliers.png"
    _save(fig, path)
    return path


def plot_correlation_heatmap(data: pd.DataFrame, output_dir: Path = IMAGE_DIR) -> Path:
    numeric = data.select_dtypes(include="number")
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(numeric.corr(), annot=True, cmap="YlGnBu", fmt=".2f", ax=ax)
    ax.set_title("Numeric Feature Correlations")
    path = output_dir / "heatmap.png"
    _save(fig, path)
    return path


def plot_sales_distribution(data: pd.DataFrame, output_dir: Path = IMAGE_DIR) -> Path:
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(data=data, x="sales", hue="region", bins=15, element="step", ax=ax)
    ax.set(title="Order Sales Distribution", xlabel="Sales", ylabel="Order count")
    path = output_dir / "sales_distribution.png"
    _save(fig, path)
    return path


def plot_dashboard(data: pd.DataFrame, output_dir: Path = IMAGE_DIR) -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    region_sales = data.groupby("region", observed=True)["sales"].sum().sort_values()
    axes[0, 0].barh(region_sales.index, region_sales.values, color="#3a7d78")
    axes[0, 0].set(title="Sales by Region", xlabel="Sales")
    sns.histplot(data=data, x="sales", bins=15, color="#e7a44a", ax=axes[0, 1])
    axes[0, 1].set(title="Order Value Distribution", xlabel="Sales")
    product_sales = data.groupby("product", observed=True)["sales"].sum().sort_values()
    axes[1, 0].bar(product_sales.index, product_sales.values, color="#507aa5")
    axes[1, 0].set(title="Sales by Product", ylabel="Sales")
    monthly = data.set_index("order_date").resample("MS")["sales"].sum()
    axes[1, 1].plot(monthly.index, monthly.values, marker="o", color="#bf5b45")
    axes[1, 1].set(title="Monthly Sales", ylabel="Sales")
    axes[1, 1].tick_params(axis="x", rotation=30)
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