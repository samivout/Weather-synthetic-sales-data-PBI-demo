from datetime import datetime

import pandas as pd
import numpy as np

from synda.globals import *
from synda.config import Config
from synda.models.salesperson_model import SimpleSalespersonModel
from synda.models.sales_locale_model import SimpleSalesLocaleModel
from synda.models.weather_model import SimpleWeatherModel
from synda.synthetic_data_generator import SyntheticDataGenerator


class TestSyntheticDataGeneratorIntegration:

    # This test accesses the FMI API. If it fails check whether the API is down or something
    # has actually broken.
    def test_synthetic_data_generator(self, sample_location_csv, sample_salespeople_csv,
                                      sample_products_csv, sample_product_locations_csv,
                                      sample_fmi_xml):

        start = datetime.fromisoformat("2025-07-01T00:00:00Z")
        end = datetime.fromisoformat("2025-07-02T00:00:00Z")
        time_interval = (start, end)

        weather_model_cls = SimpleWeatherModel
        salesperson_model_cls = SimpleSalespersonModel
        locale_model_cls = SimpleSalesLocaleModel

        config = Config(salespeople_data_filepath=sample_salespeople_csv,
                        locations_data_filepath=sample_location_csv,
                        products_data_filepath=sample_products_csv,
                        product_locations_filepath=sample_product_locations_csv)

        data_generator = SyntheticDataGenerator.construct_synthetic_data_generator(
            config=config, weather_model_cls=weather_model_cls,
            salesperson_model_cls=salesperson_model_cls,
            locale_model_cls=locale_model_cls, time_interval=time_interval
        )

        assert isinstance(data_generator, SyntheticDataGenerator)

        data = data_generator.get_sales_data()
        assert isinstance(data, dict)

        # Top-level keys are location IDs
        for loc_id, loc_data in data.items():
            assert isinstance(loc_id, int)
            # Each location value should be a dictionary keyed by salesperson ID
            assert isinstance(loc_data, dict)
            for prsn_id, df in loc_data.items():
                # Each key should be a person ID (int) or weather observation (str)
                assert isinstance(prsn_id, (int, str))
                # Each salesperson value should be a DataFrame
                assert isinstance(df, pd.DataFrame)
                # DataFrame should have expected columns
                if isinstance(prsn_id, int):
                    expected_columns = [TIMESTAMP_STR] + [prd_id for prd_id in
                                                          config.get_products_by_location_id(loc_id)[PRD_ID_STR]]
                else:
                    expected_columns = [TIMESTAMP_STR, WTHR_IDX_STR] + list(weather_model_cls.WEATHER_PARAMETERS.keys())
                for col in expected_columns:
                    assert col in df.columns

        # Check that all timestamps adhere to the interval
        for loc_data in data.values():
            for df in loc_data.values():
                # if df[TIMESTAMP_STR].apply(lambda x: isinstance(x, (float, np.floating))).any():
                #    print(f"Warning: Float values detected in {TIMESTAMP_STR} column for a dataframe.")
                if not df.empty:
                    assert df[TIMESTAMP_STR].min() >= start
                    assert df[TIMESTAMP_STR].max() <= end

        # All locations from config should appear
        assert set(data.keys()) == set(config._locations[LOC_ID_STR])

        # All salespeople per location should appear + weather observations key
        for loc_id, loc_data in data.items():
            expected_keys = config._salespeople[config._salespeople[LOC_ID_STR] == loc_id][PRS_ID_STR].tolist()
            expected_keys.append(WTHR_OBS_STR)
            assert set(loc_data.keys()) == set(expected_keys)

