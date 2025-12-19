"""
Module for base model classes that define the public APIs and common model structures.
"""

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from synda.globals import *
from synda.fetch_data import fetch_data_wfs, parse_fmi_xml
from synda.config import Config
from synda.general_functions import datetime_to_iso_z, prune_timestamps, get_init_kwargs_for_class


class BaseWeatherModel(ABC):
    """Base class for WeatherModel classes. A WeatherModel class defines the parameters that are used in the model and
    how the model computes a weather index based on those.

    Attributes
        _weather_observations (pd.DataFrame): dataframe of observations. The columns should contain at least a timestamp
            column and the parameters defined in the _weather_parameters property.
        time_interval (tuple[datetime, datetime]): tuple containing the start and end time of the interval for fething
            the weather data.
        location_id (str): the id of the location to which the weather data is to be fetched.
        url (str): the url from which the weather data is to be fetched.
        stored_query_id (str): the id of the query with which the weather data is to be fetched.
        inject_noise (bool): whether to inject noise or not in the generated data.
    """
    required_class_attributes = ["WEATHER_PARAMETERS", "WEATHER_PARAMETERS_INVERSE"]

    def __init__(self, time_interval: tuple[datetime, datetime], location_id: int,
                 location_name: str, url: str, stored_query_id: str, inject_noise: bool = False):
        """
        Initializer for BaseWeatherModel class.
        Args:
            time_interval (tuple[datetime, datetime]): tuple containing the start and end time of the interval for
                fetching the weather data.
            location_id (str): the id of the location for which the weather data is to be fetched.
            location_name (str): the name of the location for which the weather data is to be fetched.:
            url (str): the url from which the weather data is to be fetched.:
            stored_query_id (str): the id of the query with which the weather data is to be fetched.:
            inject_noise (bool): whether to inject noise or not in the generated data.:
        """

        super().__init__()
        self._weather_observations = None
        self.time_interval = time_interval
        self.location_id = location_id
        self.location_name = location_name
        self.url = url
        self.stored_query_id = stored_query_id
        self.inject_noise = inject_noise

    def __init_subclass__(cls, **kwargs):
        """
        Subclass initialization is modified to enforce the existence of the required class attributes.
        Args:
            **kwargs:
        """
        super().__init_subclass__(**kwargs)
        for attr in cls.required_class_attributes:
            if not hasattr(cls, attr):
                raise TypeError(f"{cls.__name__} must define class attribute '{attr}'")
    
    @abstractmethod
    def compute_weather_index(self) -> pd.DataFrame:
        """Public method for computing the weather index of the model. The weather index should be a value
        between 0 and 100, where 100 represents ideal weather for human pleasantness.

        Args:
            weather_observations (pd.DataFrame): dataframe of observations. The columns should contain at least
                those columns defined in the _weather_parameters property.

        Returns:
            pd.DataFrame: _description_
        """
        ...

    def get_weather_data(self) -> pd.DataFrame:
        """Returns the weather data. Ensures that data is fetched and weather index is computed.

        Returns:
            pd.DataFrame: dataframe of the weather observations.
        """
        if self._weather_observations is None:
            self.fetch_weather_observations()
        if not WTHR_IDX_STR in self._weather_observations.columns:
            self.compute_weather_index()
        return self._weather_observations

    def fetch_weather_observations(self):
        """Fetches weather data over the given timeframe from the FMI API.

        Args:
            time_stamps (pd.DataFrame): dataframe of timestamps.
        """

        # If data is already fetched, no need to fetch it again.
        if self._weather_observations is not None:
            return

        cls = self.__class__
        weather_parameters = ",".join(value for value in cls.WEATHER_PARAMETERS.values())
        params = {
            "place": self.location_name,
            "starttime": datetime_to_iso_z(self.time_interval[0]),
            "endtime": datetime_to_iso_z(self.time_interval[1]),
            "timestep": "60",
            "parameters": weather_parameters
        }

        ret = fetch_data_wfs(url=self.url, wfs_version="2.0.0", stored_query_id=self.stored_query_id,
                             query_params=params)
        
        inverse_params = cls.WEATHER_PARAMETERS_INVERSE
        parsed_values = parse_fmi_xml(ret)

        for col_name in parsed_values.columns:
            if col_name in inverse_params:
                new_name = inverse_params[col_name]
                parsed_values.rename({col_name: new_name}, inplace=True, errors="raise",
                                     axis="columns")

        parsed_values.dropna(inplace=True, axis="index")
        self._weather_observations = parsed_values

    @classmethod
    def from_row(cls, time_interval: tuple[datetime, datetime], data_row: pd.Series,
                 config: Config, inject_noise: bool = False):
        """Class method for constructing a weather model instance from a Pandas series.

        Args:
            time_interval: the interval which is used for fetching the weather data.
            data_row (pd.Series): a series containing columns for the required init data.

        Returns:
            cls: an instance of this class initialized with the series parameters.
        """
        init_kwargs = get_init_kwargs_for_class(data_row=data_row, cls=cls,
                                                include_parents=True)

        url = config.get_url()
        stored_query_id = config.get_stored_query_id()

        return cls(time_interval=time_interval, url=url, stored_query_id=stored_query_id,
                   inject_noise=inject_noise, **init_kwargs)



class BaseSalespersonModel(ABC):
    """
    Base class for modeling salespeople. Defines the expected public API that concrete classes should
    implement.

    Attributes
        person_id (int): person id
        performance_weight (float): a performance weight representing their effectiveness. Used in assigning
                the number of sales across the salespeople of a particular location.
        sales_by_product (list): a list of sales by product id for this salesperson across timestamps.
    """
    def __init__(self, person_id: int, performance_weight: float, inject_noise: bool = False):
        """
        Initializer for BaseSalespersonModel.
        Args:
            person_id (int): the person id:
            performance_weight (float): a performance weight representing their effectiveness. Used in assigning
                the number of sales across the salespeople of a particular location.
            inject_noise (bool): whether to inject noise or not to the generated data.
        """
        super().__init__()
        self._person_id = person_id
        self._performance_weight = performance_weight
        self.inject_noise = inject_noise
        self._sales_by_product = None

    @property
    def performance_weight(self) -> float:
        return self._performance_weight

    @property
    def person_id(self) -> int:
        return self._person_id
    
    @property
    def sales_by_product(self) -> pd.DataFrame | None:
        return self._sales_by_product

    def get_sales_data(self) -> tuple[int, pd.DataFrame]:
        """Get the salesdata for this salesperson as a dataframe.

        Returns:
            pd.DataFrame: a dataframe containing the sales infromation for this salesperson. 
        """
        return self.person_id, self.sales_by_product
    
    @abstractmethod
    def get_availability(self, dataframe: pd.DataFrame, timestamp_col: str = TIMESTAMP_STR) -> pd.DataFrame:
        """Method for getting the availability of this salesperson at the given timestamps.

        Args:
            dataframe (pd.DataFrame): dataframe containing at least a timestamp column.
            timestamp_col (str): the name of the timestamp column. Defaults to TIMESTAMP_STR.

        Returns:
            pd.Dataframe: a dataframe with a boolean column named by this salesperson's ID 
                stating the availability of this salesperson.
        """

    @abstractmethod
    def assign_product_ids(self, sales: int, product_ids: pd.DataFrame):
        """Assigns the given number of sales to the given product IDs. Concrete implementation
        should choose the method of assignment.

        Args:
            sales (int): number of sales to be assigned.
            product_ids (pd.DataFrame): dataframe of product IDs to be used in assignment.
        """
        ...

    @classmethod
    def from_row(cls, data_row: pd.Series, inject_noise: bool = False):
        """Class method for constructing a salesperson instance from a Pandas series.

        Args:
            data_row (pd.Series): a series containing columns for the required init data.

        Returns:
            cls: an instance of this class initialized with the series parameters.
        """
        init_kwargs = get_init_kwargs_for_class(data_row=data_row, cls=cls,
                                                include_parents=True)
        return cls(inject_noise=inject_noise, **init_kwargs)

class BaseSalesLocaleModel(ABC):
    """
    Base class for modeling the sales of a locale. Defines the public API that concrete classes
    should implement.

    location_id (int): the location id of this location.
    salespeople (list): a list of sales people assigned to this location.
    weather_model (BaseWeatherModel): a weather model assigned to this location.
    inject_noise (bool): whether to inject noise or not to the generated data.
    _product_ids (list): a list of product ids assigned to this location.
    _open_hours_start (bool): the start time of open hours.
    _open_hours_end (bool): the end time of open hours.
    _open_days_start (bool): the start weekday of open days.
    _open_days_end (bool): the end weekday of open days.
    _data_generated (bool): whether the sales data for the location has been generated or not.
    """
    def __init__(self, location_id: int, salespeople: list[BaseSalespersonModel],
                 weather_model: BaseWeatherModel, product_ids: pd.DataFrame,
                 open_hours_start: int | float = 8, open_hours_end: int | float = 20,
                 open_days_start: int = 0, open_days_end: int = 5,
                 inject_noise: bool = False):
        """
        Initialize the BaseSalesLocaleModel class with the given parameters.
        Args:
            location_id (int): the location id of this location.
            salespeople (pd.DataFrame): dataframe of sales people assigned to this location.
            weather_model (BaseWeatherModel): a weather model assigned to this location.
            product_ids (list): a list of product ids assigned to this location.
            open_hours_start (int): the start time of open hours.
            open_hours_end (int): the end time of open hours.
            open_days_start (int): the start weekday of open days.:
            open_days_end (int): the end weekday of open days.:
            inject_noise (bool): whether to inject noise or not to the generated data.:
        """
        super().__init__()
        self._location_id = location_id
        self.salespeople = salespeople
        self.weather_model = weather_model
        self.inject_noise = inject_noise
        self._product_ids = product_ids
        self._open_hours_start = open_hours_start
        self._open_hours_end = open_hours_end
        self.open_days_start = open_days_start
        self.open_days_end = open_days_end
        self._data_generated = False

    @property
    def product_ids(self) -> pd.DataFrame:
        return self._product_ids

    @property
    def location_id(self) -> int:
        return self._location_id
    
    def _prune_timestamps(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Utility method to prune timestamps from a dataframe based on closed hours and days.

        Uses the locale's open hours and open days to determine which timestamps to remove.
        Supports overnight open hours (e.g., 20:00 - 04:00).

        Args:
            dataframe (pd.DataFrame): dataframe to prune.

        Returns:
            pd.DataFrame: pruned dataframe.
        """
        start_hour = int(self._open_hours_start)
        end_hour = int(self._open_hours_end)

        # Handle overnight hours
        if start_hour < end_hour:
            open_hours = list(range(start_hour, end_hour))
        else:
            open_hours = list(range(start_hour, 24)) + list(range(0, end_hour))

        all_hours = list(range(24))
        closed_hours = [h for h in all_hours if h not in open_hours]

        start_day = self.open_days_start
        end_day = self.open_days_end
        open_days = list(range(start_day, end_day + 1))  # inclusive
        all_days = list(range(7))
        closed_days = [d for d in all_days if d not in open_days]

        return prune_timestamps(dataframe, days_to_remove=closed_days, hours_to_remove=closed_hours)
    
    def _build_availability_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Construct a combined availability DataFrame by merging each salesperson's
        availability DataFrame on 'timestamp'.

        Args:
            df (pd.DataFrame): DataFrame containing a 'timestamp' column (datetime-like).

        Returns:
            pd.DataFrame: DataFrame with:
                - 'timestamp' column,
                - one column per salesperson ID with boolean availability.
        """
        base = df[[TIMESTAMP_STR]].copy()

        for sp in self.salespeople:
            sp_df = sp.get_availability(base, timestamp_col=TIMESTAMP_STR)
            base = pd.merge(base, sp_df, on=TIMESTAMP_STR, how="left")

        return base
    
    @abstractmethod
    def _generate_locale_sales_data(self):
        """Method for generating the sales data of the locale. The method should at some point
        assign the sales down to salespeople. The concrete implementation decides how this is
        done. Following the generation the method should flip the _data_generated attribute to
        True to prevent running the generation again.

        Returns:
            pd.DataFrame: _description_
        """
        ...

    def get_sales_data(self) -> tuple[int, dict[int, pd.DataFrame]]:
        """Get sales data of the locale as a dataframe on the given timestamps.

        Args:
            time_stamps (pd.DataFrame): a dataframe of timestamps at which to get the data.

        Returns:
            pd.DataFrame: a dataframe representing the locales salesdata.
        """
        # Skip data generation if it has already been performed.
        if not self._data_generated:
            self._generate_locale_sales_data()

        locale_data_dict = {}
        for sp in self.salespeople:
            person_id, df_sales = sp.get_sales_data()
            if not isinstance(df_sales, pd.DataFrame):
                raise TypeError(
                    f"Sales data for salesperson {person_id} must be a pandas DataFrame."
                )
            locale_data_dict[person_id] = df_sales.copy(deep=True)

        locale_data_dict[WTHR_OBS_STR] = self.weather_model.get_weather_data()

        return self.location_id, locale_data_dict
    
    @classmethod
    def from_row(cls, salesperson_model_cls: type[BaseSalespersonModel], 
                 weather_model_cls: type[BaseWeatherModel], locale_data_row: pd.Series,
                 time_interval: tuple[datetime, datetime], config: Config,
                 inject_noise: bool = False) -> 'BaseSalesLocaleModel':
        """
        Class method for initializing a BaseSalesLocaleModel instance from a row of columnar data, utilizing the given
        weather model and salesperson model, time interval and config.
        Args:
            salesperson_model_cls (type[BaseSalespersonModel]): a concrete salesperson model class to use.
            weather_model_cls (type[BaseWeatherModel]): a concrete weather model class to use.
            locale_data_row (pd.Series): a single row of columnar data to use. The data should contain columns whose
                names match exactly the attributes of the class to initialize.
            time_interval (tuple[datetime, datetime]): a tuple of two datetime objects representing the time interval
                over which the synthetic sales data is generated.
            config (Config): a Config instance containing relevant parameters.

        Returns:
            BaseSalesLocaleModel: a BaseSalesLocaleModel instance.
        """
        location_id = locale_data_row[LOC_ID_STR]
        location_salespeople_df = config._salespeople[config._salespeople[LOC_ID_STR] == location_id]
        location_products_df = config.get_products_by_location_id(location_id=location_id)
        location_salespeople = []

        for idx, prsn_row in location_salespeople_df.iterrows():
            
            location_salespeople.append(
                salesperson_model_cls.from_row(prsn_row, inject_noise=inject_noise)    
            )

        weather_model = weather_model_cls.from_row(time_interval=time_interval, data_row=locale_data_row,
                                                   config=config)

        locale_kwargs = get_init_kwargs_for_class(data_row=locale_data_row, cls=cls, 
                                                  include_parents=True)
        locale_kwargs["salespeople"] = location_salespeople
        locale_kwargs["weather_model"] = weather_model
        
        return cls(product_ids=location_products_df, inject_noise=inject_noise, **locale_kwargs)

        
    @abstractmethod
    def _assign_sales(self, sales_df: pd.DataFrame, availability_df: pd.DataFrame) -> pd.DataFrame:
        """Assigns the locales sales to the encapsulated salespeople.
        """
        ...
