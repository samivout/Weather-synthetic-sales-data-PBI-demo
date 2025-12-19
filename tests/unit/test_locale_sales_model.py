import pytest
from unittest.mock import MagicMock, patch

from datetime import datetime

import pandas as pd
import numpy as np

import synda
from synda.globals import *
from synda.models.sales_locale_model import SimpleSalesLocaleModel


class TestSimpleSalesLocaleModel:

    sales_max = 5
    location_id = 1,
    start = datetime.fromisoformat("2025-09-01T00:00:00Z")
    end = datetime.fromisoformat("2025-09-01T04:00:00Z")
    inject_noise = False
    product_ids = pd.DataFrame({PRD_ID_STR: [1, 2, 3, 4, 5]})

    def test_simple_sales_locale_model_init(self, mock_weather_model, mock_salesperson_model):
        
        model = SimpleSalesLocaleModel(sales_max=self.sales_max, location_id=self.location_id,
                                       salespeople=[mock_salesperson_model], weather_model=mock_weather_model,
                                       product_ids = self.product_ids)
        
        assert model.location_id == self.location_id
        assert mock_salesperson_model in model.salespeople
        assert len(model.salespeople) == 1
        assert model.weather_model == mock_weather_model
        assert model.sales_max == self.sales_max
        pd.testing.assert_frame_equal(model.product_ids, self.product_ids)

    @pytest.mark.parametrize("timeframe", [
        (("2025-09-01T00:00:00Z", "2025-09-02T00:00:00Z"))
    ])
    def test_simple_sales_locale_model_add_daytime_effect(self, mock_weather_model, mock_salesperson_model,
                                                          hourly_dataframe, timeframe):

        model = SimpleSalesLocaleModel(sales_max=self.sales_max, location_id=self.location_id,
                                       salespeople=[mock_salesperson_model], weather_model=mock_weather_model,
                                       product_ids = self.product_ids, inject_noise=False)
        
        dataframe = hourly_dataframe(timeframe[0], timeframe[1])
        initial_length = dataframe.shape[0]
        dataframe = model._add_daytime_effect(df=dataframe, mean=12.0, sd=3.0, timestamp_col=TIMESTAMP_STR)
        final_length = dataframe.shape[0]
        
        assert initial_length == final_length
        assert DAY_EFF_STR in dataframe.columns

        # For Gaussian dependence we expect the maximum to occur at 12:00 as defined in the _add_daytime_effect call
        max_idx = dataframe[DAY_EFF_STR].idxmax()
        max_timestamp = dataframe.loc[max_idx, TIMESTAMP_STR]

        max_hour = pd.to_datetime(max_timestamp, utc=True).hour

        assert max_hour == 12, f"Expected maximum at 12:00, but got {max_hour}:00"

        df = dataframe.copy()
        df["hour"] = pd.to_datetime(df[TIMESTAMP_STR], utc=True).dt.hour
        df = df.set_index("hour")[DAY_EFF_STR]

        mean_hour = 12
        max_offset = int(min(mean_hour, df.index.max() - mean_hour))

        # Take left and right values, both including the mean. Left is reversed for assertion.
        left = df.loc[mean_hour - np.arange(0, max_offset + 1)].to_numpy()
        right = df.loc[mean_hour + np.arange(0, max_offset + 1)].to_numpy()

        assert np.allclose(left, right, rtol=1e-3, atol=1e-6)

    @pytest.mark.parametrize("timeframe", [
        (("2025-09-01T00:00:00Z", "2025-09-02T00:00:00Z"))
    ])
    def test_simple_sales_locale_model_add_daytime_effect_with_noise(self, mock_weather_model, mock_salesperson_model,
                                                                     hourly_dataframe, timeframe):

        model = SimpleSalesLocaleModel(sales_max=self.sales_max, location_id=self.location_id,
                                       salespeople=[mock_salesperson_model], weather_model=mock_weather_model,
                                       product_ids = self.product_ids, inject_noise=True)
        
        dataframe = hourly_dataframe(timeframe[0], timeframe[1])
        initial_length = dataframe.shape[0]
        dataframe = model._add_daytime_effect(df=dataframe, mean=12.0, sd=3.0, timestamp_col=TIMESTAMP_STR)
        final_length = dataframe.shape[0]
        
        assert initial_length == final_length
        assert DAY_EFF_STR in dataframe.columns

    @pytest.mark.parametrize("timeframe", [
        (("2025-09-01T00:00:00Z", "2025-09-02T00:00:00Z"))
    ])
    def test_simple_sales_locale_model_add_total_sales(self, mock_weather_model, mock_salesperson_model,
                                                       hourly_dataframe, timeframe):

        model = SimpleSalesLocaleModel(sales_max=self.sales_max, location_id=self.location_id,
                                       salespeople=[mock_salesperson_model], weather_model=mock_weather_model,
                                       inject_noise=False, product_ids=self.product_ids)
        
        dataframe = hourly_dataframe(timeframe[0], timeframe[1])
        len_dataframe = len(dataframe)
        
        # Add easily verifiable dummy values to dataframe
        dataframe[DAY_EFF_STR] = np.ones(len_dataframe) * 0.5
        dataframe[WTHR_IDX_STR] = np.ones(len_dataframe) * 0.5

        expected_sales = np.ceil(model.sales_max * np.ones(len_dataframe) * 0.5 ** 2)

        # Compute sales
        dataframe = model._add_total_sales(dataframe)

        assert SALES_STR in dataframe.columns
        assert np.allclose(expected_sales, dataframe[SALES_STR].to_numpy())

    def test_simple_sales_locale_model_build_availability_dataframe(self, simple_salesperson_factory, hourly_dataframe,
                                                                    mock_weather_model):
        
        base_timeframe = hourly_dataframe("2025-09-01T00:00:00Z", "2025-09-02T00:00:00Z")
        salespeople = []

        # Assign dummy return values to salespeople and gather into list.
        for i in range (4):
            salesperson = simple_salesperson_factory(person_id=i)
            dummy_return_value = pd.DataFrame({TIMESTAMP_STR: base_timeframe[TIMESTAMP_STR], i: [0] * len(base_timeframe[TIMESTAMP_STR])})
            salesperson.get_availability.return_value = dummy_return_value
            salespeople.append(salesperson)

        # Init model.
        model = SimpleSalesLocaleModel(sales_max=self.sales_max, location_id=self.location_id,
                                       salespeople=salespeople, weather_model=mock_weather_model,
                                       inject_noise=False, product_ids=self.product_ids)
        
        # Get availability form model.
        availability = model._build_availability_dataframe(base_timeframe)

        # Construct expected value of the model output.
        expected_availability = base_timeframe.copy()
        if "value" in expected_availability.columns:
            expected_availability.drop("value", inplace=True, axis=1)
        for i in range(4):
            expected_availability[i] = [0] * len(base_timeframe[TIMESTAMP_STR])

        pd.testing.assert_frame_equal(expected_availability, availability)

    def test_simple_sales_locale_model_assign_sales(self, simple_salesperson_factory, mock_weather_model):
        
        timestamps = pd.date_range("2025-09-01 10:00", periods=3, freq="H")
        sales_df = pd.DataFrame({
            TIMESTAMP_STR: timestamps,
            SALES_STR: [100, 200, 300] # total locale sales per hour
        })

        salespeople = []

        # Assign dummy return values to salespeople and gather into list.
        for i in range (1, 5):
            mock_return_value = MagicMock()
            salesperson = simple_salesperson_factory(person_id=i, performance_weight=float(i))
            salespeople.append(salesperson)

        # Availability matrix: 1, 2, 3, 4 columns
        availability_df = pd.DataFrame({
            TIMESTAMP_STR: timestamps,
            1: [1, 1, 0],   # salesperson 1 unavailable at last timestamp
            2: [1, 0, 1],   # 2 unavailable at middle timestamp
            3: [1, 1, 1],   # 3 always available
            4: [0, 1, 1],   # 4 unavailable first timestamp
        })

        # Compute expected values manually
        # Weights: 1=1, 2=2, 3=3, 4=4
        expected = []
        for i, row in availability_df.iterrows():
            avail = np.array([row[1], row[2], row[3], row[4]])
            weights = np.array([1, 2, 3, 4])
            weighted = avail * weights
            norm = weighted / weighted.sum() if weighted.sum() else np.zeros_like(weighted)
            assigned = norm * sales_df.loc[i, SALES_STR]
            expected.append(assigned)
        expected = np.ceil(np.vstack(expected))

        product_ids = pd.DataFrame({PRD_ID_STR: [1, 2, 3]})

        # Init model.
        model = SimpleSalesLocaleModel(sales_max=self.sales_max, location_id=self.location_id,
                                       salespeople=salespeople, weather_model=mock_weather_model,
                                       inject_noise=False, product_ids=product_ids)
        
        result = SimpleSalesLocaleModel._assign_sales(model, sales_df, availability_df)

        # Verify assignment math
        np.testing.assert_allclose(result[[1,2,3,4]].to_numpy(), expected, rtol=1e-6)

        # Verify all salespeople were called with expected per-person sales
        for sp in model.salespeople:
            assert sp.assign_product_ids.called
            call_df = sp.assign_product_ids.call_args[0][0]
            # Check that the total assigned to this salesperson matches expected
            np.testing.assert_allclose(call_df[SALES_STR].to_numpy(), result[sp.person_id].to_numpy())

    def test_simple_sales_locale_model_get_sales_data(self, simple_salesperson_factory, mock_weather_model):
        # Dummy sales data.
        df_sp1 = pd.DataFrame({
            TIMESTAMP_STR: pd.date_range("2025-10-01", periods=3, freq="H", tz="UTC"),
            1: [1, 2, 3],
            2: [0, 1, 0],
        })

        df_sp2 = pd.DataFrame({
            TIMESTAMP_STR: pd.date_range("2025-10-01", periods=3, freq="H", tz="UTC"),
            1: [5, 4, 3],
            2: [2, 2, 1],
        })
        
        salesdata = [df_sp1, df_sp2]
        salespeople = []

        # Assign dummy return values to salespeople and gather into list.
        for i in range (2):
            mock_return_value = MagicMock()
            salesperson = simple_salesperson_factory(person_id=i)
            salesperson.get_sales_data.return_value = (i, salesdata[i])
            salespeople.append(salesperson)

        # Init model.
        model = SimpleSalesLocaleModel(sales_max=self.sales_max, location_id=self.location_id,
                                       salespeople=salespeople, weather_model=mock_weather_model,
                                       inject_noise=False, product_ids=self.product_ids)
        
        # Brute-force to skip data generation call in unit test condition.
        model._data_generated = True
        location_id, sales_dict = model.get_sales_data()

        # Assertions
        assert set(sales_dict.keys()) == {0, 1, WTHR_OBS_STR}

        pd.testing.assert_frame_equal(sales_dict[0], df_sp1)
        pd.testing.assert_frame_equal(sales_dict[1], df_sp2)

        # Verify copies, not references, by modifying original.
        df_sp1.loc[0, 1] = 999
        df_sp2.loc[0, 2] = 999

        assert sales_dict[0].loc[0, 1] == 1
        assert sales_dict[1].loc[0, 2] == 2

    def test_simple_sales_locale_model_from_row(self, mock_config):

        time_interval = (datetime.fromisoformat("2025-09-01T00:00:00Z"), datetime.fromisoformat("2025-09-02T00:00:00Z"))

        # --- Prepare locale row ---
        locale_row = pd.Series({LOC_ID_STR: 1, "Name": "Helsinki", "sales_max": 20})

        # --- Prepare mocked salesperson and weather classes ---
        salesperson_mock_cls = MagicMock()
        salesperson_mock_instance = MagicMock()
        salesperson_mock_cls.from_row.return_value = salesperson_mock_instance

        weather_mock_cls = MagicMock()
        weather_mock_instance = MagicMock()
        weather_mock_cls.from_row.return_value = weather_mock_instance

        # --- Call from_row ---
        result = SimpleSalesLocaleModel.from_row(
            salesperson_model_cls=salesperson_mock_cls,
            weather_model_cls=weather_mock_cls,
            locale_data_row=locale_row,
            config=mock_config,
            time_interval=time_interval
        )

        # --- Assertions ---
        # Instance type
        assert isinstance(result, SimpleSalesLocaleModel)

        # Locale-level kwargs are set
        assert result.location_id == 1

        # Correct number of salespeople returned (matching location_id)
        assert len(result.salespeople) == 2
        for sp in result.salespeople:
            assert sp is salesperson_mock_instance  # all mock instances

        # Weather model set correctly
        assert result.weather_model is weather_mock_instance

        # Ensure from_row was called on salesperson class for each relevant row
        assert salesperson_mock_cls.from_row.call_count == 2
        # Ensure weather model from_row called once
        weather_mock_cls.from_row.assert_called_once_with(data_row=locale_row, time_interval=time_interval,
                                                          config=mock_config)