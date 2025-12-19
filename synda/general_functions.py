"""
Module for general functions used in various places.
"""

import inspect
from pathlib import Path
from datetime import datetime, time, timezone, timedelta

import pandas as pd

from synda.globals import *


def datetime_to_iso_z(dt: datetime) -> str:
    """
    Convert a datetime object to ISO 8601 string with 'Z' suffix (UTC).

    Args:
        dt (datetime): The datetime object to convert.

    Returns:
        str: ISO 8601 formatted string, e.g., "2025-09-01T00:00:00Z".
    """
    # Ensure datetime is in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def prune_timestamps(df, timestamp_col=TIMESTAMP_STR, days_to_remove=None, hours_to_remove=None):
    """
    Prune timestamps from the DataFrame according to day-of-week and/or hour rules,
    without creating new columns.

    Args:
        df (pd.DataFrame): Input dataframe with a timestamp column.
        timestamp_col (str): Name of the timestamp column.
        days_to_remove (list[int], optional): Days to remove (0=Monday, 6=Sunday).
        hours_to_remove (list[int], optional): Hours to remove (0-23).

    Returns:
        pd.DataFrame: Copy of the dataframe with timestamps pruned.
    """
    # Ensure timestamp column is datetime
    timestamps = pd.to_datetime(df[timestamp_col], utc=True)

    mask = pd.Series(True, index=df.index)

    if days_to_remove is not None:
        mask &= ~timestamps.dt.dayofweek.isin(days_to_remove)

    if hours_to_remove is not None:
        mask &= ~timestamps.dt.hour.isin(hours_to_remove)

    return df[mask].copy()


def get_init_kwargs_for_class(
    data_row: pd.Series, cls: type, include_parents: bool = False) -> dict[str, any]:
    """
    Given a class with a set of required parameters for instantiating, this function
    returns a dictionary of kwargs based off of the required parameters and the values in
    the given series.

    Args:
        data_row (pd.Series): a Pandas series containing at least the required arguments.
        cls (type): the class to inspect.
        include_parents (bool): if True, collect parameters from parent classes' __init__ as well.

    Returns:
        dict[str, Any]: a dictionary of kwargs for instantiating the given class.
    """
    param_names = set()

    # Collect parameters from the class __init__ (excluding self)
    sig = inspect.signature(cls.__init__)
    param_names.update(p.name for p in sig.parameters.values() if p.name != "self")

    if include_parents:
        for base in cls.__mro__[1:]:  # skip cls itself
            if hasattr(base, "__init__"):
                base_sig = inspect.signature(base.__init__)
                param_names.update(p.name for p in base_sig.parameters.values() if p.name != "self")

    # Filter the row to only include keys that match parameters
    filtered_kwargs = {k: v for k, v in data_row.items() if k in param_names}

    return filtered_kwargs


def number_to_time_of_day(value: int | float) -> time:

    base = datetime(1900, 1, 1)  # arbitrary date
    time_obj = (base + timedelta(hours=value)).time()

    return time_obj


def flatten_sales_and_weather_data(nested_data: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Converts the nested sales dictionary into flat DataFrames suitable for fact tables.
    Separates sales data and weather data.

    Args:
        nested_data (dict):
            {location_id: {salesperson_id: df_of_hourly_sales_by_product, "Weather data": df_weather}}

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]:
            - sales_df with columns [location_id, person_id, product_id, timestamp, sales]
            - weather_df with columns [location_id, timestamp, ...other weather columns...]
    """
    sales_frames = []
    weather_frames = []

    for location_id, data_dict in nested_data.items():
        for key, df in data_dict.items():
            df_copy = df.copy()
            df_copy[LOC_ID_STR] = location_id

            if isinstance(key, int):
                # Salesperson data: melt product columns into long form
                product_cols = [col for col in df.columns if col not in {TIMESTAMP_STR, LOC_ID_STR, PRS_ID_STR}]
                melted_df = df_copy.melt(
                    id_vars=[TIMESTAMP_STR, LOC_ID_STR],
                    value_vars=product_cols,
                    var_name=PRD_ID_STR,
                    value_name=SALES_STR
                )
                melted_df[PRD_ID_STR] = melted_df[PRD_ID_STR].astype(int)
                melted_df[PRS_ID_STR] = key
                sales_frames.append(melted_df)
            elif key == WTHR_OBS_STR:
                # Weather data
                weather_frames.append(df_copy)

    # Concatenate all frames once
    sales_df = pd.concat(sales_frames, ignore_index=True) if sales_frames else pd.DataFrame()
    weather_df = pd.concat(weather_frames, ignore_index=True) if weather_frames else pd.DataFrame()

    # Ensure consistent column order for sales_df
    if not sales_df.empty:
        sales_df = sales_df[[LOC_ID_STR, PRS_ID_STR, PRD_ID_STR, TIMESTAMP_STR, SALES_STR]]

    return sales_df, weather_df


def unflatten_sales_and_weather_data(
    sales_df: pd.DataFrame,
    weather_df: pd.DataFrame
) -> dict[int, dict[int | str, pd.DataFrame]]:
    """
    Reconstructs the nested dictionary structure from flattened sales and weather DataFrames.
    Each salesperson's dataframe has timestamps as rows and product_id as separate columns.

    Args:
        sales_df (pd.DataFrame): flat sales table with columns
            [location_id, person_id, product_id, timestamp, sales]
        weather_df (pd.DataFrame): flat weather table with columns
            [location_id, timestamp, ...weather columns...]

    Returns:
        dict[int, dict[int | str, pd.DataFrame]]:
            {
                location_id: {
                    salesperson_id: df_of_sales (timestamps x products),
                    "Weather data": df_of_weather
                }
            }
    """
    nested_data = {}

    # Rebuild sales data
    if not sales_df.empty:
        # Pivot to get product columns for each salesperson
        for (loc_id, person_id), group_df in sales_df.groupby([LOC_ID_STR, PRS_ID_STR]):
            if loc_id not in nested_data:
                nested_data[loc_id] = {}

            pivot_df = group_df.pivot(
                index=TIMESTAMP_STR,
                columns=PRD_ID_STR,
                values=SALES_STR
            ).reset_index()
            pivot_df.columns.name = None

            nested_data[loc_id][person_id] = pivot_df

    # Rebuild weather data
    if not weather_df.empty:
        for loc_id, group_df in weather_df.groupby(LOC_ID_STR):
            if loc_id not in nested_data:
                nested_data[loc_id] = {}

            nested_data[loc_id][WTHR_OBS_STR] = group_df.drop(
                columns=[LOC_ID_STR]
            ).reset_index(drop=True)

    return nested_data

def get_delta_table_root_path() -> Path:

    current_dir = Path.cwd()
    if current_dir.name == ".jupytext-sync-ipynb":
        return current_dir.parent.parent.parent.parent / "data" / "delta"
    elif current_dir.name == "notebooks":
        return current_dir.parent.parent.parent / "data" / "delta"
    elif current_dir.name == "Samin_PBI_demo":
        return current_dir.parent / "data" / "delta"
    else:
        raise IOError("Can't dynamically infer path.")


def get_config_root_path() -> Path:
    current_dir = Path.cwd()
    if current_dir.name == ".jupytext-sync-ipynb":
        return current_dir.parent.parent.parent / "config"
    elif current_dir.name == "notebooks":
        return current_dir.parent.parent / "config"
    elif current_dir.name == "Samin_PBI_demo":
        return current_dir / "config"
    else:
        raise IOError("Can't dynamically infer path.")


def split_datetime_range(
    start: datetime,
    end: datetime,
    max_range_delta: int = MAX_RANGE_DELTA
) -> list[tuple[datetime, datetime]]:
    """
    Splits a datetime interval into contiguous sub-ranges of at most max_range_delta length.
    This function is mainly used to split date ranges into fitting ranges for FMI's API.

    The returned ranges fully cover the original interval without gaps or overlaps.
    Each sub-range follows a start-inclusive, end-exclusive convention.

    Args:
        start (datetime): Inclusive start of the overall time interval.
        end (datetime): Exclusive end of the overall time interval.
        max_range_delta (int): the max range of hours to include in each subrange.

    Returns:
        list[tuple[datetime, datetime]]:
            A list of (sub_start, sub_end) tuples where each interval spans
            no more than 440 hours and together they fully cover the original
            [start, end) interval.

    Raises:
        ValueError: If `end` is less than or equal to `start`.
    """
    max_range_time_delta = timedelta(hours=max_range_delta)

    if end <= start:
        raise ValueError("end must be strictly greater than start")

    ranges: list[tuple[datetime, datetime]] = []
    current_start = start

    while current_start < end:
        current_end = min(current_start + max_range_time_delta, end)
        ranges.append((current_start, current_end))
        current_start = current_end

    return ranges