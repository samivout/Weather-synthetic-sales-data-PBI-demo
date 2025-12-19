import pytest

from pathlib import Path
from datetime import datetime

import pandas as pd

from synda.models.weather_model import SimpleWeatherModel
from synda.config import Config


class TestIntegrationSimpleWeatherModel:

    stored_query_id = "fmi::observations::weather::hourly::timevaluepair"
    url = "https://opendata.fmi.fi/wfs"
    start = datetime.fromisoformat("2025-09-01T00:00:00Z")
    end = datetime.fromisoformat("2025-09-01T04:00:00Z")
    time_interval = (start, end)

    def test_simple_weather_model_fetch_data(self, sample_location_csv, sample_salespeople_csv):
        """Full integration test with the config based on the testdata csv file.
        This test accesses the FMI API.
        """
        location_id = 1
        temp_opt = 22.0
        rain_threshold = 0.5
        temp_tol_range = 13.0
        inject_noise = True

        model = SimpleWeatherModel(time_interval=self.time_interval, location_id=location_id,
                                   temp_opt=temp_opt, rain_threshold=rain_threshold,
                                   temp_tol_range=temp_tol_range, inject_noise=inject_noise,
                                   location_name="Helsinki", url=self.url,
                                   stored_query_id=self.stored_query_id)
        
        model.fetch_weather_observations()
        assert model._weather_observations is not None
        