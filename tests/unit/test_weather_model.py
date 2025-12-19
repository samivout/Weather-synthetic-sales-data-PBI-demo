import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from datetime import datetime

import synda
from synda.models.weather_model import SimpleWeatherModel


class TestSimpleWeatherModel:

    start = datetime.fromisoformat("2025-09-01T00:00:00Z")
    end = datetime.fromisoformat("2025-09-01T04:00:00Z")
    time_interval = (start, end)
    location_id = 1
    temp_opt = 22.0
    rain_threshold = 0.5
    temp_tol_range = 13.0
    inject_noise = True
    dummy_url = "dummy_url"
    dummy_name = "dummy_name"
    dummy_stored_query_id = "dummy_stored_query_id"

    def test_simple_weather_model_init_success(self):

        model = SimpleWeatherModel(time_interval=self.time_interval, location_id=self.location_id,
                                   temp_opt=self.temp_opt, rain_threshold=self.rain_threshold,
                                   temp_tol_range=self.temp_tol_range, inject_noise=self.inject_noise,
                                   location_name=self.dummy_name, url=self.dummy_url,
                                   stored_query_id=self.dummy_stored_query_id)
        
        assert model.time_interval == self.time_interval
        assert model.location_id == self.location_id
        assert model.temp_opt == self.temp_opt
        assert model.rain_threshold == self.rain_threshold
        assert model.temp_tol_range == self.temp_tol_range
        assert model.inject_noise == self.inject_noise
        assert model.url == self.dummy_url
        assert model.stored_query_id == self.dummy_stored_query_id
        assert model.location_name == self.dummy_name

    def test_simple_weather_model_fetch_weather_observations(self):

        fetch_ret = "fetch_dummy"
        parse_ret = pd.DataFrame({"dummy": [1, 2, 3]})
        inverse_ret = {"inv_dummy": "dummy"}
        fetch_wfs_patch = patch.object(synda.models.base_models, synda.models.base_models.fetch_data_wfs.__name__,
                                       return_value=fetch_ret)
        parse_fmi_xml_patch = patch.object(synda.models.base_models, synda.models.base_models.parse_fmi_xml.__name__,
                                           return_value=parse_ret)
        inverse_parmas_patch = patch.object(synda.models.weather_model.SimpleWeatherModel,
                                            "WEATHER_PARAMETERS_INVERSE", inverse_ret)

        with (fetch_wfs_patch as mock_fetch, parse_fmi_xml_patch as mock_parse, inverse_parmas_patch):

            model = SimpleWeatherModel(time_interval=self.time_interval, location_id=self.location_id,
                                       temp_opt=self.temp_opt, rain_threshold=self.rain_threshold,
                                       temp_tol_range=self.temp_tol_range, inject_noise=self.inject_noise,
                                       location_name=self.dummy_name, url=self.dummy_url,
                                       stored_query_id=self.dummy_stored_query_id)

            model.fetch_weather_observations()

        mock_fetch.assert_called_once()
        mock_parse.assert_called_once_with(fetch_ret)
        pd.testing.assert_frame_equal(parse_ret, model._weather_observations)

