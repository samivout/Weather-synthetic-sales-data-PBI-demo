import pytest
from unittest.mock import MagicMock, patch

from datetime import datetime

import pandas as pd
import numpy as np

from synda.globals import *
from synda.config import Config

# Tests in this module heavily depend on the testdata remaining as is. If these tests fail, first check
# whether the data has been changed instead of something actually being broken.

class TestConfig:

    def test_config_init(self, sample_location_csv, sample_salespeople_csv,
                         sample_products_csv, sample_product_locations_csv):
        
        config = Config(locations_data_filepath=sample_location_csv,
                        salespeople_data_filepath=sample_salespeople_csv,
                        products_data_filepath=sample_products_csv,
                        product_locations_filepath=sample_product_locations_csv)
        
        assert isinstance(config._locations, pd.DataFrame)
        assert isinstance(config._salespeople, pd.DataFrame)
        assert isinstance(config._products, pd.DataFrame)
        assert isinstance(config._product_locations, pd.DataFrame)

    def test_config_get_location_name(self, sample_location_csv, sample_salespeople_csv,
                                      sample_products_csv, sample_product_locations_csv):
        
        config = Config(locations_data_filepath=sample_location_csv,
                        salespeople_data_filepath=sample_salespeople_csv,
                        products_data_filepath=sample_products_csv,
                        product_locations_filepath=sample_product_locations_csv)
        
        expected_loc_name = "Helsinki"
        loc_name = config.get_location_name(1)

        assert expected_loc_name == loc_name

    def test_config_get_salesperson_name(self, sample_location_csv, sample_salespeople_csv,
                                         sample_products_csv, sample_product_locations_csv):
        
        config = Config(locations_data_filepath=sample_location_csv,
                        salespeople_data_filepath=sample_salespeople_csv,
                        products_data_filepath=sample_products_csv,
                        product_locations_filepath=sample_product_locations_csv)
        
        expected_prs_name = "Veera Miettinen"
        prs_name = config.get_salesperson_name(1)

        assert expected_prs_name == prs_name

    def test_config_get_products_by_location(self, sample_location_csv, sample_salespeople_csv,
                                             sample_products_csv, sample_product_locations_csv):
        
        config = Config(locations_data_filepath=sample_location_csv,
                        salespeople_data_filepath=sample_salespeople_csv,
                        products_data_filepath=sample_products_csv,
                        product_locations_filepath=sample_product_locations_csv)
        
        expected_prd_ids = pd.DataFrame({PRD_ID_STR: [1, 2, 3, 4, 5, 6, 8],
                                         LOC_ID_STR: [1, 1, 1, 1, 1, 1, 1]})
        expected_prd_ids = expected_prd_ids.astype({PRD_ID_STR: Int64Dtype(), LOC_ID_STR: Int64Dtype()})
        prd_ids = config.get_products_by_location_id(1)

        pd.testing.assert_frame_equal(expected_prd_ids.reset_index(drop=True),
                                      prd_ids.reset_index(drop=True))
        
    def test_config_get_open_hours_by_location(self, sample_location_csv, sample_salespeople_csv,
                                               sample_products_csv, sample_product_locations_csv):
        
        config = Config(locations_data_filepath=sample_location_csv,
                        salespeople_data_filepath=sample_salespeople_csv,
                        products_data_filepath=sample_products_csv,
                        product_locations_filepath=sample_product_locations_csv)
        
        expected_open_hours = (8, 16)
        open_hours = config.get_open_hours_by_location_id(1)

        assert expected_open_hours == open_hours
