"""
Module for functions used in parsing parameters from config files.
"""

from pathlib import Path

import pandas as pd

from synda.globals import *


class Config:
    """
    A common config class that can be used to access config data and provide parameters elsewhere in the project.

    Attributes:
        _locations (pd.DataFrame): Dataframe containing location dim data.
        _salespeople (pd.DataFrame): Dataframe containing sales people dim data.
        _products (pd.DataFrame): Dataframe containing products dim data.
        _product_locations (pd.DataFrame): Dataframe containing product location dim data.
        _stored_query_id (str): The id of the stored query used with FMI API.
        _url (str): The url used to access the FMI API.
    """
    def __init__(self, locations_data_filepath: str | Path,
                 salespeople_data_filepath: str | Path,
                 products_data_filepath: str | Path,
                 product_locations_filepath: str | Path):
        
        self._locations = pd.read_csv(locations_data_filepath, sep=";", dtype=TARGET_DTYPES)
        self._salespeople = pd.read_csv(salespeople_data_filepath, sep=";", dtype=TARGET_DTYPES)
        self._products = pd.read_csv(products_data_filepath, sep=";", dtype=TARGET_DTYPES)
        self._product_locations = pd.read_csv(product_locations_filepath, sep=";", dtype=TARGET_DTYPES)

        self._stored_query_id = "fmi::observations::weather::hourly::timevaluepair"
        self._url = "https://opendata.fmi.fi/wfs"

    def get_location_name(self, location_id: int) -> str:
        """Get the name corresponding to a location_id."""
        row = self._locations.loc[self._locations[LOC_ID_STR] == location_id]
        if row.empty:
            raise ValueError(f"Location ID {location_id} not found in config")
        return row[LOC_NAME_STR].iloc[0]
    
    def get_salesperson_name(self, salesperson_id: int) -> str:
        """Get the name corresponding to a salesperson_id."""
        row = self._salespeople.loc[self._salespeople[PRS_ID_STR] == salesperson_id]
        if row.empty:
            raise ValueError(f"Person_ID {salesperson_id} not found in config")
        return row[PRS_NAME_STR].iloc[0]
    
    def get_products_by_location_id(self, location_id: int) -> pd.DataFrame:
        """Get product IDs by location ID.

        Args:
            location_id (int): interger representing a location's ID.

        Returns:
            pd.DataFrame: a DataFrame containing the product IDs available at the given location.
        """
        product_ids = self._product_locations[self._product_locations[LOC_ID_STR] == location_id]
        return product_ids
    
    def get_open_hours_by_location_id(self, location_id: int) -> tuple[int, int]:
        """Get open hours by location ID.

        Args:
            location_id (int): integer representing a location's ID.

        Returns:
            tuple[int, int]: tuple representing the start and end of open hours.
        """
        row = self._locations[self._locations[LOC_ID_STR] == location_id]
        start, end = int(row[LOC_AVB_HRS_BG_STR]), int(row[LOC_AVB_HRS_ED_STR])
        return start, end

    def get_open_hours(self) -> pd.DataFrame:
        """Get open hours for all locations.

        Returns:
            pd.DataFrame: a DataFrame containing all open hours for all locations.
        """
        return self._locations[[LOC_ID_STR, LOC_AVB_HRS_BG_STR, LOC_AVB_HRS_ED_STR]].copy()

    def get_stored_query_id(self) -> str:
        return self._stored_query_id
    
    def get_url(self) -> str:
        return self._url