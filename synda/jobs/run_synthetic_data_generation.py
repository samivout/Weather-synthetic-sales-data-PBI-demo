from datetime import datetime
from pathlib import Path

from typing import Type

from synda.config import Config
from synda.synthetic_data_generator import SyntheticDataGenerator
from synda.data_io import DeltaWriter
from synda.general_functions import flatten_sales_and_weather_data, split_datetime_range
from synda.models.base_models import BaseSalesLocaleModel, BaseSalespersonModel, BaseWeatherModel
from synda.globals import *

def run_synthetic_data_generation_process(
    start: datetime,
    end: datetime,
    config_dir: Path,
    delta_base_dir: Path,
    weather_model_cls: Type[BaseWeatherModel],
    locale_model_cls: Type[BaseSalesLocaleModel],
    salesperson_model_cls: Type[BaseSalespersonModel], 
    inject_noise: bool = True,
):
    """Public function for running the synthetic data generation process. Splits the given time interval
    into fitting ranges for the FMI API and runs the process repeatedly until all datetimes in the range
    have been consumed.

    Args:
        subrange_start (datetime): start of time range
        subrange_end (datetime): end of time range
        config_dir (Path): path to directory containing config files.
        delta_base_dir (Path): path to delta table base dir.
        inject_noise (bool, optional): Whether to inject noise to the generated data. Defaults to True.
    """
    list_of_subranges = split_datetime_range(start=start, end=end, max_range_delta=MAX_RANGE_DELTA)
    for subrange in list_of_subranges:
        _run_synthetic_data_generation_single_interval(subrange_start=subrange[0],
                                                       subrange_end=subrange[1],
                                                       config_dir=config_dir,
                                                       delta_base_dir=delta_base_dir,
                                                       weather_model_cls=weather_model_cls,
                                                       locale_model_cls=locale_model_cls,
                                                       salesperson_model_cls=salesperson_model_cls,
                                                       inject_noise=inject_noise)


def _run_synthetic_data_generation_single_interval(
    subrange_start: datetime,
    subrange_end: datetime,
    config_dir: Path,
    delta_base_dir: Path,
    weather_model_cls: Type[BaseWeatherModel],
    locale_model_cls: Type[BaseSalesLocaleModel],
    salesperson_model_cls: Type[BaseSalespersonModel],
    inject_noise: bool = True,
):
    """Internal function for running the synthetic data generation process on a time interval
    the FMI API accepts.

    Args:
        subrange_start (datetime): start of time range
        subrange_end (datetime): end of time range
        config_dir (Path): path to directory containing config files.
        delta_base_dir (Path): path to delta table base dir.
        inject_noise (bool, optional): Whether to inject noise to the generated data. Defaults to True.
    """
    time_interval = (subrange_start, subrange_end)

    config = Config(
        salespeople_data_filepath=config_dir / "Salespeople config.csv",
        locations_data_filepath=config_dir / "Location config.csv",
        products_data_filepath=config_dir / "Product config.csv",
        product_locations_filepath=config_dir / "Product location config.csv",
    )

    data_generator = SyntheticDataGenerator.construct_synthetic_data_generator(
        config=config,
        weather_model_cls=weather_model_cls,
        salesperson_model_cls=salesperson_model_cls,
        locale_model_cls=locale_model_cls,
        time_interval=time_interval,
        inject_noise=inject_noise,
    )

    data = data_generator.get_sales_data()
    sales_data, weather_data = flatten_sales_and_weather_data(data)

    writer = DeltaWriter(base_path=delta_base_dir)

    writer.write_table(
        df=sales_data,
        table_name="test_sales_data",
        mode="merge",
        merge_keys=[LOC_ID_STR, PRS_ID_STR, PRD_ID_STR, TIMESTAMP_STR],
        update_latest=True,
    )

    writer.write_table(
        df=weather_data,
        table_name="test_weather_data",
        mode="merge",
        merge_keys=[LOC_ID_STR, TIMESTAMP_STR],
        update_latest=True,
    )
