"""
Module for data IO functionality, discounting web APIs.
"""
import os
import shutil
import glob
from pathlib import Path
import pandas as pd
import logging
from deltalake import DeltaTable, write_deltalake
from deltalake.exceptions import TableNotFoundError
from typing import Optional

logger = logging.getLogger(__name__)


class DeltaWriter:
    """
    A backend class for writing and managing Delta Lake tables. Written with mainly local systems in mind. Might work
    with cloud-based storage systems.

    Attributes:
        base_path (str): the root directory of the delta tables.
        storage_options (dict): _description_. Defaults to None.
    """

    def __init__(self, base_path: str, storage_options: Optional[dict] = None):
        """Initializes a new DeltaWriter instance, creating the directory structure given by base_path if it doesn't exist.
        Storage options can be given by the optional storage_options argument.

        Args:
            base_path (str): the root directory of the delta tables.
            storage_options (Optional[dict], optional): _description_. Defaults to None.
        """
        self.base_path = Path(base_path)
        self.storage_options = storage_options or {}
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_table_path(self, table_name: str) -> str:
        return str(self.base_path / table_name)

    def write_table(self, df: pd.DataFrame, table_name: str, mode: str = "overwrite",
                    merge_keys: Optional[list[str]] = None, update_latest: bool = False) -> None:
        """Method for writing a dataframe into a delta table. Allowed modes are append, overwrite and merge, defaulting to 
        overwrite.

        Args:
            df (pd.DataFrame): dataframe to write into a delta table.
            table_name (str): the name of the target table.
            mode (str, optional): append | overwrite | merge. Defaults to "overwrite".
            merge_keys (Optional[list[str]], optional): If using merge mode, keys upon which the merge is based on.
                Defaults to None.
            update_latest: whether to update a statically named parquet file with the latest version of the data.
        """
        table_path = self._get_table_path(table_name)

        if mode == "merge":
            self._merge_table(df, table_path, merge_keys)
        else:
            write_deltalake(
                table_path,
                df,
                mode=mode,
                storage_options=self.storage_options,
            )
            logger.info(f"Wrote table '{table_name}' in mode '{mode}'")

        if update_latest:
            self._update_latest_snapshot(table_path, table_name)

    def _merge_table(self, df: pd.DataFrame, table_path: str, merge_keys: list[str]) -> None:
        """Method for merging the given dataframe and target delta table.

        Args:
            df (pd.DataFrame): the dataframe to merge.
            table_path (str): path to the delta table to merge the dataframe into.
            merge_keys (list[str]): keys upon which the merge is based on.
        """
        try:
            table = DeltaTable(table_path, storage_options=self.storage_options)
            existing_df = table.to_pandas()
            merged_df = (
                pd.concat([existing_df, df])
                .drop_duplicates(subset=merge_keys, keep="last")
                .reset_index(drop=True)
            )
            write_deltalake(
                table_path,
                merged_df,
                mode="overwrite",
                storage_options=self.storage_options,
            )
            logger.info(f"Merged table at {table_path}")

        except TableNotFoundError:
            write_deltalake(
                table_path,
                df,
                mode="overwrite",
                storage_options=self.storage_options,
            )
            logger.info(f"Created new table '{table_path}'")

    def _update_latest_snapshot(self, table_path: str, table_name: str) -> None:
        """
        Finds the newest Parquet file in the Delta table directory
        and copies it as <table_name>_latest.parquet in the same base path.
        """
        parquet_files = glob.glob(f"{table_path}/*.parquet")
        if not parquet_files:
            logger.warning(f"No Parquet files found for table '{table_name}'")
            return

        latest_file = max(parquet_files, key=os.path.getctime)
        latest_copy_path = self.base_path / f"{table_name}_latest.parquet"

        shutil.copy(latest_file, latest_copy_path)
        logger.info(f"Updated latest snapshot: {latest_copy_path}")

    def read_table(self, table_name: str) -> pd.DataFrame:
        """Method for reading delta table into a dataframe.

        Args:
            table_name (str): name of the target table.

        Returns:
            pd.DataFrame: the table data as a dataframe.
        """
        table_path = self._get_table_path(table_name)
        table = DeltaTable(table_path, storage_options=self.storage_options)
        return table.to_pandas()

    def table_exists(self, table_name: str) -> bool:
        try:
            _ = DeltaTable(self._get_table_path(table_name), storage_options=self.storage_options)
            return True
        except TableNotFoundError:
            return False
