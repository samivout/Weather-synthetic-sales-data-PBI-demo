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
# Eploratory notebook for fetching data from the Finnish Meteorological Institute's open data API. The notebook is used to explore fetching data from the FMI API and seeing what is returned.
# First we import the required default, dependency and local packages and modules:

# %%
from pathlib import Path

import pandas as pd
from owslib.wfs import WebFeatureService

from synda.fetch_data import parse_fmi_xml, fetch_data_wfs
from synda.data_io import DeltaWriter

current_file_dirpath = Path().resolve()
project_root_dirpath = current_file_dirpath.parent.parent
delta_table_base_path = project_root_dirpath.parent / "data" / "delta"
writer = DeltaWriter(base_path=delta_table_base_path)

URL = "https://opendata.fmi.fi/wfs"
wfs = WebFeatureService(url=URL, version="2.0.0")

# %% [markdown]
# Next we'll define the parameters of the WFS query. The stored_query_id points us to the desired endpoint and with the parameters we define the details of the query. Additionally build and print the query URL manually for inspection in case problems occur.

# %%
# PRA_PT1H_ACC, TA_PT1H_AVG
# Dummy query specification before more programmatic approach.
stored_query_id = "fmi::observations::weather::hourly::timevaluepair"
params = {
    "place": "Kajaani",
    "starttime": "2025-07-01T12:00:00Z",
    "endtime": "2025-07-01T16:00:00Z",
    "timestep": "60",
    "parameters": "TA_PT1H_AVG,PRA_PT1H_ACC"
}

# Build query string
query = f"{URL}?service=WFS&version=2.0.0&request=getFeature&storedquery_id={stored_query_id}"
for k, v in params.items():
    query += f"&{k}={v}"

print(query)

xml_content = fetch_data_wfs(url=URL, wfs_version="2.0.0", stored_query_id=stored_query_id, query_params=params)

# %%
# Parse and inspect XML
df = parse_fmi_xml(xml_content)
print(df.head())
