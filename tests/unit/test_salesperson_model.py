import pytest
from unittest.mock import MagicMock, patch

from datetime import datetime, time, timedelta

import pandas as pd
import numpy as np

import synda
from synda.globals import *
from synda.models.salesperson_model import SimpleSalespersonModel

class TestSimpleSalesPersonModel:

    working_hours_start, working_hours_end = 10, 18
    person_id = 3
    performance_weight = 10.0
    inject_noise = False
    start = datetime.fromisoformat("2025-09-01T00:00:00Z")
    end = datetime.fromisoformat("2025-09-01T04:00:00Z")

    def test_simple_sales_person_model_init(self):
        
        model = SimpleSalespersonModel(working_hours_start=self.working_hours_start,
                                       working_hours_end=self.working_hours_end,
                                       performance_weight = self.performance_weight,
                                       inject_noise = self.inject_noise,
                                       person_id = self.person_id)

        base = datetime(1900, 1, 1)  # arbitrary date

        working_hours_start_time = (base + timedelta(hours=self.working_hours_start)).time()
        working_hours_end_time = (base + timedelta(hours=self.working_hours_end)).time()

        assert model.working_hours_start == working_hours_start_time
        assert model.working_hours_end == working_hours_end_time
        assert model.person_id == self.person_id
        assert model.inject_noise == self.inject_noise

    @pytest.mark.parametrize("timeframe", [
        (("2025-09-01T00:00:00Z", "2025-09-02T00:00:00Z"))
    ])
    def test_simple_sales_person_model_get_availability(self, hourly_dataframe, timeframe):

        model = SimpleSalespersonModel(working_hours_start=self.working_hours_start,
                                       working_hours_end=self.working_hours_end,
                                       performance_weight=self.performance_weight,
                                       inject_noise=self.inject_noise,
                                       person_id=self.person_id)
        
        dataframe = hourly_dataframe(timeframe[0], timeframe[1])
        initial_length = dataframe.shape[0]
        availability = model.get_availability(dataframe=dataframe, timestamp_col=TIMESTAMP_STR)
        final_length = availability.shape[0]

        assert initial_length == final_length
        assert model.person_id in availability.columns

        hours = dataframe[TIMESTAMP_STR].dt.hour
        expected_values = ((hours >= 10) & (hours < 18)).to_numpy()

        expected_df = pd.DataFrame({
            TIMESTAMP_STR: dataframe[TIMESTAMP_STR],
            model.person_id: expected_values
        })

        pd.testing.assert_frame_equal(availability.reset_index(drop=True), expected_df)

    @pytest.mark.parametrize("inject_noise", [True, False])
    def test_simple_salesperson_model_assign_product_ids(self, inject_noise):

        model = SimpleSalespersonModel(working_hours_start=self.working_hours_start,
                                       working_hours_end=self.working_hours_end,
                                       performance_weight=self.performance_weight,
                                       inject_noise=self.inject_noise,
                                       person_id=self.person_id)

        sales_df = pd.DataFrame({
            TIMESTAMP_STR: pd.to_datetime(["2025-09-01T10:00:00Z", "2025-09-01T11:00:00Z"]),
            SALES_STR: [3, 5]  # total sales per timestamp
        })

        product_ids_df = pd.DataFrame({
            PRD_ID_STR: ["P1", "P2"]
        })

        model.assign_product_ids(sales_df, product_ids_df)
        result = model._sales_by_product

        # Shape: 2 timestamps × 2 products
        assert result.shape == (2, 3)  # timestamp + 2 product columns

        # Timestamp column matches input
        pd.testing.assert_series_equal(result[TIMESTAMP_STR], sales_df[TIMESTAMP_STR], check_names=False)

        # All sales are non-negative integers
        product_cols = ["P1", "P2"]
        assert (result[product_cols] >= 0).all().all()
        assert np.issubdtype(result[product_cols].values.dtype, np.integer)

        # Total sales per timestamp match input
        totals = result[product_cols].sum(axis=1)
        pd.testing.assert_series_equal(totals, sales_df[SALES_STR], check_names=False)

        # For inject_noise=False, check uniform distribution
        if not inject_noise:
            # Base sales per product
            expected_base = sales_df[SALES_STR] // len(product_ids_df)
            remainder = sales_df[SALES_STR] % len(product_ids_df)

            # Each row should have either base or base+1 sales
            for i, row in result[product_cols].iterrows():
                row_values = sorted(row)
                assert row_values[0] == expected_base[i]
                assert row_values[1] == expected_base[i] + remainder[i]  # if remainder>0

    def test_simple_salesperson_model_get_salesperson_data(self):
        pass

