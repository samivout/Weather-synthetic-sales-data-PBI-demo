"""
Module stub for mathematical and statistical functions.
"""
import pandas as pd

from synda.globals import *
from synda.config import Config


def compute_mean_sales_by_hour(sales_df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """
    Compute the mean sales by hour from the sales dataframe, resulting in a dataframe with
    24 temporal entries. The computation ignores a locale's closed hours, computing the mean only
    from the open hours of a particular locale.
    Args:
        sales_df: dataframe containing sales data.
        config: Config object.

    Returns:
        pd.DataFrame: dataframe containing the mean sales per hour.
    """
    sales_df["hour"] = sales_df[TIMESTAMP_STR].dt.hour
    open_hours = config.get_open_hours()

    working_df = sales_df.merge(open_hours, on=LOC_ID_STR, how="left")
    mask = (working_df["hour"] >= working_df[LOC_AVB_HRS_BG_STR]) & (working_df["hour"] < working_df[LOC_AVB_HRS_ED_STR])
    df_open = working_df[mask]

    mean_sales_by_hour = df_open.groupby("hour")[SALES_STR].mean()

    return mean_sales_by_hour



