import pytest
from unittest.mock import MagicMock, patch

from datetime import datetime

import pandas as pd
import numpy as np

import synda
from synda.models.salesperson_model import SimpleSalespersonModel
from synda.models.weather_model import SimpleWeatherModel
from synda.models.sales_locale_model import SimpleSalesLocaleModel
from synda.config import Config
from synda.general_functions import datetime_to_iso_z
from synda.globals import *

class TestSimpleSalesLocalModelIntegration:

    dummy_url = "dummy_url"
    dummy_name = "dummy_name"
    dummy_stored_query_id = "dummy_stored_query_id"

    def test_simple_sales_locale_model_data_flow(self, sample_location_csv, sample_salespeople_csv,
                                                 sample_products_csv, sample_product_locations_csv,
                                                 sample_fmi_xml):
        
        start_datetime = datetime.fromisoformat("2025-09-01T00:00:00Z")
        end_datetime = datetime.fromisoformat("2025-09-01T04:00:00Z")
        time_interval = (start_datetime, end_datetime)
        config = Config(salespeople_data_filepath=sample_salespeople_csv,
                        locations_data_filepath=sample_location_csv,
                        products_data_filepath=sample_products_csv,
                        product_locations_filepath=sample_product_locations_csv)

        salespeople = []
        number_of_salespeople = 4
        product_ids = [1, 2, 3, 4]
        
        for i in range(number_of_salespeople):

            salesperson = SimpleSalespersonModel(performance_weight=float(2 * (i+1)),
                                                 person_id=i, inject_noise=False,
                                                 working_hours_start=8,
                                                 working_hours_end=16)
            salespeople.append(salesperson)

        fetch_patch = patch.object(synda.models.base_models,
                                   synda.models.base_models.fetch_data_wfs.__name__,
                                   return_value=sample_fmi_xml.read_bytes())
        
        weather_model = SimpleWeatherModel(temp_opt=21.0, rain_threshold=0.5,
                                           temp_tol_range=15.0, time_interval=time_interval, location_id=1,
                                           inject_noise=False, url=self.dummy_url, location_name=self.dummy_name,
                                           stored_query_id=self.dummy_stored_query_id)
        
        sales_locale_model = SimpleSalesLocaleModel(sales_max=50, inject_noise=False,
                                                    location_id=1,
                                                    product_ids=pd.DataFrame({PRD_ID_STR:product_ids}),
                                                    weather_model=weather_model,
                                                    salespeople=salespeople)
        
        with fetch_patch:
            loc_id, sales_data_dict = sales_locale_model.get_sales_data()

        assert isinstance(sales_data_dict, dict)

        for i in range(number_of_salespeople):
            
            df = sales_data_dict[i]
            assert isinstance(df, pd.DataFrame)
            for id in product_ids:
                assert id in df.columns
                

