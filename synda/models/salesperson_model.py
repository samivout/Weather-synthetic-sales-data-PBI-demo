import pandas as pd
import numpy as np

from datetime import time

from synda.globals import *
from synda.general_functions import number_to_time_of_day
from synda.models.base_models import BaseSalespersonModel


class SimpleSalespersonModel(BaseSalespersonModel):
    """
    A class for modeling a salesperson. Inherits from BaseSalespersonModel. Implements availability via a simple
    comparison of the working hours against the given timestamps. Product assignment is handled by uniformly
    distributing assigned hourly sales across the available product IDs.

    Attributes:
        _working_hours_start (int): the starting working hours of this salesperson.
        _working_hours_end (int): the ending working hours of this salesperson.
    """
    def __init__(self, working_hours_start: int | float | time = 8.0,
                 working_hours_end: int | float | time = 16.0, **kwargs):
        """

        Args:
            working_hours_start: starting working hours of the salesperson.
            working_hours_end: ending working hours of the salesperson.
            **kwargs:
        """
        super().__init__(**kwargs)

        if isinstance(working_hours_start, (int, float)):
            working_hours_start = number_to_time_of_day(working_hours_start)
        if isinstance(working_hours_end, (int, float)):
            working_hours_end = number_to_time_of_day(working_hours_end)

        self._working_hours_start = working_hours_start
        self._working_hours_end = working_hours_end

    @property
    def working_hours_start(self) -> time:
        return self._working_hours_start

    @property
    def working_hours_end(self) -> time:
        return self._working_hours_end

    def get_availability(self, dataframe, timestamp_col = TIMESTAMP_STR) -> pd.DataFrame:
        """Get the availability of this salesperson. The availability is modeled via simple tuple
        representing the start and end working hours of this salesperson, which are used to generate
        a numpy array of available hours.

        Args:
            dataframe (pd.DataFrame): dataframe containing at least a timestamp column.
            timestamp_col (str): the name of the timestamp column. Defaults to TIMESTAMP_STR.

        Returns:
            pd.DataFrame: a dataframe with a boolean column named by the salesperson id,
                stating the availability of this salesperson.
        """
        hours = dataframe[timestamp_col].dt.hour

        available = (
                (hours >= self.working_hours_start.hour) &
                (hours < self.working_hours_end.hour)
        )

        return pd.DataFrame({
            TIMESTAMP_STR: dataframe[timestamp_col],
            self.person_id: available
        })

    def assign_product_ids(self, sales_df: pd.DataFrame, product_ids: pd.DataFrame):
        """
        Vectorized assignment of sales across products for multiple timestamps,
        producing a wide-format DataFrame.
    
        Args:
            sales_df (pd.DataFrame): DataFrame with columns 'timestamp' and 'sales'.
            product_ids (pd.DataFrame): DataFrame with at least 'Product ID' column.
    
        Side effect:
            Stores result in self._sales_by_product (wide format) with:
            - 'timestamp' column
            - one column per product ID
        """
        if PRD_ID_STR not in product_ids.columns:
            raise ValueError("product_ids must contain 'Product ID' column")
        if TIMESTAMP_STR not in sales_df.columns or SALES_STR not in sales_df.columns:
            raise ValueError("sales_df must contain 'timestamp' and 'sales' columns")
    
        df_products = product_ids.copy()
        product_cols = df_products[PRD_ID_STR].to_list()
        n_products = len(product_cols)
        n_timestamps = len(sales_df)
    
        total_sales = sales_df[SALES_STR].to_numpy()  # shape (T,)
    
        if self.inject_noise:
            # Repeat row indices according to sales counts
            row_idx = np.repeat(np.arange(n_timestamps), total_sales)
            # Random product indices
            col_idx = np.random.randint(0, n_products, size=row_idx.size)
            # Accumulate counts into matrix
            assigned_matrix = np.zeros((n_timestamps, n_products), dtype=int)
            np.add.at(assigned_matrix, (row_idx, col_idx), 1)
        else:
            # Perfectly uniform distribution
            base = total_sales // n_products
            remainder = total_sales % n_products
            assigned_matrix = np.tile(base[:, None], (1, n_products))
    
            if np.any(remainder > 0):
                # Randomly distribute remainder per timestamp
                for t_idx, r in enumerate(remainder):
                    if r > 0:
                        extra_indices = np.random.choice(n_products, size=r, replace=False)
                        assigned_matrix[t_idx, extra_indices] += 1
    
        # Build wide-format DataFrame
        df_result = pd.DataFrame(assigned_matrix, columns=product_cols)
        df_result.insert(0, TIMESTAMP_STR, sales_df[TIMESTAMP_STR].to_numpy())
    
        self._sales_by_product = df_result