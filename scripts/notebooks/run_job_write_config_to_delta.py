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
# This notebook is utilized to write the .csv file contents from the config directory into delta tables. 

# %%
from pathlib import Path

import pandas as pd

from synda.globals import *
from synda.data_io import DeltaWriter

# %%
config_dir = Path.cwd().parent.parent.parent / "config"
print(config_dir)
location_config = config_dir / "Location config.csv"
product_config = config_dir / "Product config.csv"
product_location_config = config_dir / "Product location config.csv"
salesperson_config = config_dir / "Salespeople config.csv"
product_category_config = config_dir / "Product category config.csv"

location_df = pd.read_csv(location_config, sep=";", dtype=TARGET_DTYPES)
product_df = pd.read_csv(product_config, sep=";", dtype=TARGET_DTYPES)
product_location_df = pd.read_csv(product_location_config, sep=";", dtype=TARGET_DTYPES)
salesperson_df = pd.read_csv(salesperson_config, sep=";", dtype=TARGET_DTYPES)
product_category_df = pd.read_csv(product_category_config, sep=";", dtype=TARGET_DTYPES)

# %%
delta_test_data_dir = Path.cwd().parent.parent.parent.parent / "data" / "delta"
writer = DeltaWriter(base_path=delta_test_data_dir)

location_merge_keys = [LOC_ID_STR]
product_merge_keys = [PRD_ID_STR]
product_location_merge_keys = [PRD_ID_STR, LOC_ID_STR]
salesperson_merge_keys = [PRS_ID_STR]
product_category_merge_keys = [PRD_CAT_ID_STR]

# %%
writer.write_table(df=location_df, table_name="test_location_data",
                   mode="overwrite", merge_keys=location_merge_keys, update_latest=True)

# %%
writer.write_table(df=product_df, table_name="test_product_data",
                   mode="overwrite", merge_keys=product_merge_keys, update_latest=True)

# %%
writer.write_table(df=product_location_df, table_name="test_product_location_data",
                   mode="overwrite", merge_keys=product_location_merge_keys, update_latest=True)

# %%
writer.write_table(df=salesperson_df, table_name="test_salesperson_data",
                   mode="overwrite", merge_keys=salesperson_merge_keys, update_latest=True)

# %%
writer.write_table(df=product_category_df, table_name="test_product_category_data",
                   mode="overwrite", merge_keys=product_category_merge_keys, update_latest=True)
