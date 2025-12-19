"""
Module for the overall process of generating synthetic data.
"""
from typing import Type
from datetime import datetime

import pandas as pd

from synda.models.base_models import BaseSalespersonModel, BaseWeatherModel, BaseSalesLocaleModel
from synda.config import Config


class SyntheticDataGenerator:
    """
    Class for generating synthetic sales data over a given time window for a set of locale models.

    Attributes:
        location_models (list): a list of locale models.
        _time_interval (tuple[datetime, datetime]): the time interval over which to generate synthetic data.
    """
    def __init__(self, location_models: list[BaseSalesLocaleModel], time_interval: tuple[datetime, datetime]):
        """
        Initialize the SyntheticDataGenerator class.
        Args:
            location_models: a list of locale models.
            time_interval: the time interval over which to generate synthetic data.
        """
        self.location_models = location_models
        self._time_interval = time_interval

    @property
    def time_interval(self) -> tuple[datetime, datetime]:
        return self._time_interval
    
    def get_sales_data(self) -> dict[int, dict[int, pd.DataFrame]]:
        """Collects the salesdata of the encapsulated locations into a nested dictionary with
        the top-level keys being location ids and the second-level keys being salesperson ids,
        which finally map into the hourly salesdata of each salesperson by product id.

        Returns:
            dict[int, dict[int, pd.DataFrame]]: nested dictionary, top-level keys for location id,
            second-level keys for salesperson id, mapping to salesperson hourly sales by product id
            represented by a dataframe.
        """
        locale_dict = {}
        for loc in self.location_models:
            location_id, location_data_dict = loc.get_sales_data()
            locale_dict[location_id] = location_data_dict

        return locale_dict
    
    @classmethod
    def construct_synthetic_data_generator(
        cls,
        time_interval: tuple[datetime, datetime],
        weather_model_cls: Type[BaseWeatherModel],
        locale_model_cls: Type[BaseSalesLocaleModel],
        salesperson_model_cls: Type[BaseSalespersonModel],
        config: Config,
        inject_noise: bool = False
    ) -> 'SyntheticDataGenerator':
        
        location_models = []

        for idx, loc_row in config._locations.iterrows():

            location_models.append(
                locale_model_cls.from_row(salesperson_model_cls=salesperson_model_cls,
                                          weather_model_cls=weather_model_cls,
                                          locale_data_row=loc_row, config=config,
                                          time_interval=time_interval,
                                          inject_noise=inject_noise)
            )

        return cls(time_interval=time_interval, location_models=location_models)
