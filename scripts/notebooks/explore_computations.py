# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
#   kernelspec:
#     display_name: synda-CY3SfM5I-py3.13
#     language: python
#     name: python3
# ---

# %% [markdown]
# This notebook is utilized for exploring computations on the data saved to delta tables. The main purpose of these is to act as a scratch book referencepoint for Power BI DAX computations.

# %%
from datetime import datetime
from pathlib import Path

import pandas as pd

from synda.globals import *
from synda.config import Config
from synda.data_io import DeltaWriter
from synda.general_functions import flatten_sales_and_weather_data, get_delta_table_root_path, get_config_root_path
from synda.computations import compute_mean_sales_by_hour

# %% [markdown]
# We'll initialize a DeltaWriter for reading data from the required delta tables. Along that we'll also initialize a Config instance.

# %%
print(Path.cwd())
delta_test_data_dir = get_delta_table_root_path()
print(delta_test_data_dir)
writer = DeltaWriter(base_path=delta_test_data_dir)

config_dir = get_config_root_path()
location_config = config_dir / "Location config.csv"
product_config = config_dir / "Product config.csv"
product_location_config = config_dir / "Product location config.csv"
salespeople_config = config_dir / "Salespeople config.csv"

config = Config(salespeople_data_filepath=salespeople_config,
                locations_data_filepath=location_config,
                products_data_filepath=product_config,
                product_locations_filepath=product_location_config)

# %%
sales_data = writer.read_table(table_name="test_sales_data")
weather_data = writer.read_table(table_name="test_weather_data")
location_data = writer.read_table(table_name="test_location_data")

# %% [markdown]
# With the data read into memory, we can start doing some reference computations.

# %%
print(sales_data.head)

# %%
sales_data['hour'] = sales_data[TIMESTAMP_STR].dt.hour

mean_sales_per_hour = (
    sales_data.groupby('hour')[SALES_STR]
        .mean()
        .reset_index()
        .sort_values('hour')
)

mean_hourly_sales = sales_data.mean().reset_index()
mean_hourly_sales_fn = compute_mean_sales_by_hour(sales_data, config=config)

# %%
print("Hourly sales naive: \n")
print(mean_sales_per_hour.head)
print("Hourly sales fn result: \n")
print(mean_hourly_sales_fn.head)


# %%
print(mean_hourly_sales.head)

# %% [markdown]
# Next we'll compute the correlation coefficient between sales and weather index.

# %%
merged_sales_and_weather_data = sales_data.merge(
    weather_data[[LOC_ID_STR, TIMESTAMP_STR, WTHR_IDX_STR]],
    on=[LOC_ID_STR, TIMESTAMP_STR],
    how="left"
)

# %%
corr_df = merged_sales_and_weather_data[[SALES_STR, WTHR_IDX_STR, LOC_ID_STR, TIMESTAMP_STR]]
print(corr_df)
corr_df = corr_df[corr_df[LOC_ID_STR] == 1]
correlation = corr_df.corr(method="pearson")
print(correlation)

# %%
corr_df = corr_df.set_index(TIMESTAMP_STR)
daily_means = corr_df.resample("D").mean().reset_index()
print(daily_means)

# %%
correlation_for_daily_mean = daily_means.corr(method="pearson")
print(correlation_for_daily_mean)
