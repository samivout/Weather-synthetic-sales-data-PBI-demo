# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: .jupytext-sync-ipynb//ipynb,py:percent
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
# This notebook is utilized for generating synthetic data for a given batch of weather observations and a config of salespeople.

# %%
from datetime import datetime

from synda.globals import *
from synda.models.salesperson_model import SimpleSalespersonModel
from synda.models.sales_locale_model import SimpleSalesLocaleModel
from synda.models.weather_model import SimpleWeatherModel
from synda.general_functions import get_config_root_path, get_delta_table_root_path
from synda.jobs import run_synthetic_data_generation_process

# %% [markdown]
# We'll initialize the parameters for the synthetic data generation process, which are the time interval from which to fetch the data, the model classes to utilize, paths to config and delta roots and whether to inject noise into the generated data or not.

# %%
start = datetime.fromisoformat("2025-06-01T00:00:00Z")
end = datetime.fromisoformat("2025-08-31T00:00:00Z")

weather_model_cls = SimpleWeatherModel
salesperson_model_cls = SimpleSalespersonModel
locale_model_cls = SimpleSalesLocaleModel

config_dir = get_config_root_path()
delta_table_root_dir = get_delta_table_root_path()

inject_noise = True

# %% [markdown]
# Fianlly we'll run the data generation process via the Synda jobs function.

# %%
run_synthetic_data_generation_process(
    start=start,
    end=end,
    config_dir=config_dir,
    delta_base_dir=delta_table_root_dir,
    weather_model_cls=SimpleWeatherModel,
    locale_model_cls=SimpleSalesLocaleModel,
    salesperson_model_cls=SimpleSalespersonModel,
    inject_noise=inject_noise
)
