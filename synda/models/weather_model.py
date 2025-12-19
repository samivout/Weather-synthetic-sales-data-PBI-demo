from datetime import datetime

import pandas as pd

from synda.globals import *
from synda.models.base_models import BaseWeatherModel

class SimpleWeatherModel(BaseWeatherModel):
    """
    Simple weather model class that models the pleasantness of the weather via deviations of temperature
    from ideal and accumulated rain exceeding a threshold value. Inherits from BaseWeatherModel.

    Attributes:
        temp_opt (float): what the model considers the optimal temperature.
        rain_threshold (float): what the model considers as the threshold for negative effects due to
        temp_tol_range (float): determines how strong the negative effect of deviating from the optimal temperature.
    """
    WEATHER_PARAMETERS = {
        "Temperature": "TA_PT1H_AVG",
        "Rain amount": "PRA_PT1H_ACC"
    }
    WEATHER_PARAMETERS_INVERSE = {
        "TA_PT1H_AVG": "Temperature",
        "PRA_PT1H_ACC": "Rain amount"
    }

    def __init__(self, temp_opt: float = 21.0, rain_threshold: float = 0.5,
                 temp_tol_range: float = 15.0, **kwargs):
        """
        Initialize a SimpleWeatherModel object with the given parameters.
        Args:
            temp_opt (float): what the model considers the optimal temperature.
            rain_threshold (float): what the model considers as the threshold for negative effects due to rainfall.
            temp_tol_range (float): determines how strong the negative effect of deviating from the optimal temperature is.
            **kwargs:
        """
        super().__init__(**kwargs)
        self.temp_opt = temp_opt
        self.rain_threshold = rain_threshold
        self.temp_tol_range = temp_tol_range

    def compute_weather_index(self):
        """Computes a weather index (0.0-1.0) based on temperature and rainfall,
        using the self._weather_observations dataframe and weather parameter attributes.

        The result is added as a new column 'Weather index' to self._weather_observations
        if it doesn't already exist.
        """
        df = self._weather_observations

        # Safety check: avoid recomputation if already exists
        if WTHR_IDX_STR in df.columns:
            return

        if not all(col in df.columns for col in self.WEATHER_PARAMETERS.keys()):
            raise ValueError("Missing required columns 'Temperature' and 'Rain amount'.")

        # Vectorized computation
        df[WTHR_IDX_STR] = (
            100
            - (abs(df["Temperature"] - self.temp_opt) / self.temp_tol_range * 50)
            - (df["Rain amount"] / self.rain_threshold * 50)
        )

        # Clamp to [0, 100] to avoid negatives or >100 values due to outliers
        df[WTHR_IDX_STR] = df[WTHR_IDX_STR].clip(lower=0, upper=100).values / 100
    
