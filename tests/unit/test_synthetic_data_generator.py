import pytest
from unittest.mock import MagicMock, patch

from datetime import datetime

import pandas as pd
import numpy as np

import synda
from synda.globals import *
from synda.synthetic_data_generator import SyntheticDataGenerator


class TestSyntheticDataGenerator:

    start = datetime.fromisoformat("2025-09-01T00:00:00Z")
    end = datetime.fromisoformat("2025-09-01T04:00:00Z")
    time_interval = (start, end)

    def test_synthetic_data_generator_init(self, mock_locale_model):
        
        data_generator = SyntheticDataGenerator(time_interval=self.time_interval,
                                                location_models=[mock_locale_model])
        
        assert data_generator.time_interval == self.time_interval
        assert len(data_generator.location_models) == 1
        assert mock_locale_model in data_generator.location_models

    def test_synthetic_data_generator_get_sales_data(self, mock_locale_model):

        data_generator = SyntheticDataGenerator(time_interval=self.time_interval,
                                                location_models=[mock_locale_model])

        sales_dict = data_generator.get_sales_data()

        assert isinstance(sales_dict, dict)
        assert len(sales_dict) == len(data_generator.location_models)
        assert sales_dict[1] == "dummy"

    def test_construct_synthetic_data_generator_calls_locale_model(self, mock_config):

        # Mock weather and salesperson classes
        mock_weather_cls = MagicMock(name="WeatherModel")
        mock_salesperson_cls = MagicMock(name="SalesPersonModel")

        # Mock locale_model_cls and its from_row method
        mock_locale_cls = MagicMock(name="LocaleModel")
        mock_locale_instance_1 = MagicMock()
        mock_locale_instance_2 = MagicMock()

        # Configure from_row to return different mocks for each call
        mock_locale_cls.from_row.side_effect = [mock_locale_instance_1, mock_locale_instance_2]

        generator = SyntheticDataGenerator.construct_synthetic_data_generator(
            time_interval=self.time_interval,
            weather_model_cls=mock_weather_cls,
            locale_model_cls=mock_locale_cls,
            salesperson_model_cls=mock_salesperson_cls,
            config=mock_config
        )

        # Ensure from_row was called once per location row
        assert mock_locale_cls.from_row.call_count == len(mock_config._locations[LOC_ID_STR])

        # Ensure from_row called with expected kwargs for the first row
        first_call_kwargs = mock_locale_cls.from_row.call_args_list[0][1]
        assert first_call_kwargs["locale_data_row"][LOC_ID_STR] == 1
        assert first_call_kwargs["salesperson_model_cls"] == mock_salesperson_cls
        assert first_call_kwargs["weather_model_cls"] == mock_weather_cls
        assert first_call_kwargs["config"] == mock_config

        # Ensure the location_models list in the resulting generator matches mocked instances
        assert generator.location_models == [mock_locale_instance_1, mock_locale_instance_2]

        # Check that the time_window was passed correctly
        assert generator.time_interval == self.time_interval