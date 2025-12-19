"""
Module for parametrized fixtures.
"""
import pytest
import pandas as pd

from synda.globals import *


@pytest.fixture
def hourly_dataframe() -> pd.DataFrame:
    """
    Returns a factory function that generates a dataframe with hourly timestamps
    and increasing values.
    """
    def _factory(start: str, end: str) -> pd.DataFrame:
        """
        Args:
            start (str): Start timestamp (ISO format, e.g., "2025-10-15T00:00:00").
            end (str): End timestamp (ISO format, e.g., "2025-10-16T00:00:00").
            
        Returns:
            pd.DataFrame: DataFrame with columns:
                - TIMESTAMP_STR: hourly timestamps from start to end (inclusive of start, exclusive of end)
                - "value": integers starting from 0
        """
        timestamps = pd.date_range(start=start, end=end, freq="H", inclusive="both")
        values = list(range(len(timestamps)))
        return pd.DataFrame({TIMESTAMP_STR: timestamps, "value": values})
    
    return _factory