# Data Cleaning & Visualization Analysis

## Project Overview

This project focuses on cleaning raw data, handling missing values, removing duplicates, detecting outliers, and generating meaningful visual insights using Python.

The objective is to transform messy datasets into structured information that can support data-driven decision making.

## Technologies Used

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Jupyter Notebook

## Data Cleaning Steps

- Missing Value Treatment
- Duplicate Record Removal
- Data Type Conversion
- Outlier Detection using IQR Method
- Data Validation

## Visualizations

- Missing Value Analysis
- Sales Distribution
- Regional Analysis
- Correlation Heatmap
- Outlier Detection Boxplots
- Business Insights Dashboard

## Key Skills Demonstrated

- Data Cleaning
- Exploratory Data Analysis
- Data Visualization
- Statistical Analysis
- Business Intelligence

## Project Outcome

Successfully transformed raw data into meaningful business insights through preprocessing, analysis, and visualization techniques.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.visualization
```

The command reads `data/sales_data.csv`, writes `data/cleaned_sales_data.csv`, and saves plots to `images/`. Open `notebooks/data_cleaning_analysis.ipynb` for the interactive version. The sample data intentionally includes missing values, duplicate rows, inconsistent labels, and an unusually large order. Outliers are flagged for review, not silently removed.

## Project Structure

```text
data/       Raw and generated cleaned sales data
notebooks/  Interactive analysis
src/        Reusable cleaning and visualization functions
images/     Generated plots
reports/    Analysis report
```