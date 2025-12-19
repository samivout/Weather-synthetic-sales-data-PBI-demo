import pytest
from unittest.mock import MagicMock, patch

from datetime import datetime

import pandas as pd
import numpy as np

import synda.computations as scp
from synda.globals import *
from synda.config import Config
from synda.data_io import DeltaWriter

# Tests in this module heavily depend on the testdata remaining as is. If these tests fail, first check
# whether the data has been changed instead of something actually being broken.

class TestIntegrationComputations:

    def test_compute_mean_sales_by_hour(self, sample_delta_root, sample_location_csv, sample_salespeople_csv,
                                        sample_products_csv, sample_product_locations_csv):

        config = Config(locations_data_filepath=sample_location_csv,
                        salespeople_data_filepath=sample_salespeople_csv,
                        products_data_filepath=sample_products_csv,
                        product_locations_filepath=sample_product_locations_csv)

        delta_writer = DeltaWriter(base_path=sample_delta_root)

        sales_df = delta_writer.read_table("test_sales_data")

        sales_by_hour = scp.compute_mean_sales_by_hour(sales_df=sales_df, config=config)

        assert isinstance(sales_by_hour, pd.Series)