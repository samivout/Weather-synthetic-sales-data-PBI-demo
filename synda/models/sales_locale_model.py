import numpy as np
import pandas as pd

from synda.globals import *
from synda.models.base_models import BaseSalesLocaleModel


class SimpleSalesLocaleModel(BaseSalesLocaleModel):
    """A model for generating synthetic sales data based off of observed weather, datetime and salesperson.
    Initially a Poisson distribution is used as a baseline to assign an expected mean for sales per hour. The homogenous
    Poisson process is then simulated into a non-homogenous one by modifying the baseline mean by the effects of the
    previously listed features. This modification is used to reject a certain amount of sales to model the dynamic
    effects. One such model is suppposed to be used for one location, as implied by the weather dependency.

    Inherits attributes and methods from BaseSalesLocaleModel.

    Attributes
        sales_max (float): Maximum sales per hour. Used as a capping value in simulating draws from a non-homogenous
            Poisson distribution.
    """

    def __init__(self, sales_max: int = 200, **kwargs):
        """
        Initializes a SimpleSalesLocalModel class with the given parameters.
        Args:
            sales_max (float): Maximum sales per hour.
        """
        super().__init__(**kwargs)
        self.sales_max = sales_max

    def _generate_locale_sales_data(self):
        """Method for running synthetic data generation for the given weather observations, location configs and

        Returns:
            pd.DataFrame: _description_
        """
        main_df = self.weather_model.get_weather_data()
        main_df = self._prune_timestamps(main_df)
        main_df = self._add_daytime_effect(df=main_df, mean=14.0, sd=3.0)
        main_df = self._add_total_sales(df=main_df)
        availability_df = self._build_availability_dataframe(main_df)
        self._assign_sales(sales_df=main_df, availability_df=availability_df)
        
        return
    
    def _add_total_sales(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add a SALES_STR column to the dataframe using weather and daytime effects.
        The weather index and daytime effect are used as multipliers to scale down the
        sales from the max due to non-ideal conditions.
    
        Args:
            df (pd.DataFrame): DataFrame containing at least the columns:
                               - WTHR_IDX_STR (0-1)
                               - DAY_EFF_STR (0-1)
                               - TIMESTAMP_STR (not used for computation but must exist)
        
        Returns:
            pd.DataFrame: the input dataframe with an additional 'Locale sales' column.
        """
        # Draw initial Poisson sales for each timestamp
        if self.inject_noise:
            initial_sales = np.random.poisson(lam=self.sales_max, size=len(df))
        else:
            initial_sales = np.ones(len(df)) * self.sales_max
        
        # Compute non-homogeneous scaling factor
        scaling_factor = (df[WTHR_IDX_STR].values) * df[DAY_EFF_STR].values
        
        # Apply the scaling and round to integers.
        df[SALES_STR] = np.ceil(initial_sales * scaling_factor)

        return df

    def _add_daytime_effect(self, df: pd.DataFrame, mean: float, sd: float,
                            timestamp_col: str = TIMESTAMP_STR) -> pd.DataFrame:
        """
        Add a DAY_EFF_STR column to the dataframe in-place using a Gaussian function
        of the hour of day. The effect for each timestamp is computed as the value of the
        Gaussian defined by the input parameters. The output values fall in the range [0, 1].

        Args:
            df (pd.DataFrame): Input dataframe with a timestamp column.
            timestamp_col (str): Name of the timestamp column.
            mean (float): Mean of the Gaussian (center hour of day).
            sd (float): Standard deviation of the Gaussian.

        Returns:
            None: Modifies df in-place.
        """
        timestamps = pd.to_datetime(df[timestamp_col], utc=True)
        hours = timestamps.dt.hour.values.astype(float)

        # Base Gaussian daytime effect
        base_effect = np.exp(-((hours - mean) ** 2) / (2 * sd ** 2))

        if not self.inject_noise:
            df[DAY_EFF_STR] = base_effect
            return df

        rng = np.random.default_rng()

        # Per-day amplitude variation
        day_index = timestamps.dt.floor("D")
        unique_days = day_index.unique()

        daily_noise = rng.lognormal(
            mean=0.0,
            sigma=0.15,  # controls day-to-day variability
            size=len(unique_days),
        )

        daily_noise_map = dict(zip(unique_days, daily_noise))
        day_scaling = day_index.map(daily_noise_map).values

        # Per-timestamp multiplicative noise
        point_noise = rng.lognormal(
            mean=0.0,
            sigma=0.05,  # small local variation
            size=len(df),
        )

        noisy_effect = base_effect * day_scaling * point_noise

        # Temporal smoothing
        noisy_effect = (
            pd.Series(noisy_effect, index=timestamps)
            .rolling(window=3, center=True, min_periods=1)
            .mean()
            .values
        )

        # Clamp to [0, 1]
        df[DAY_EFF_STR] = np.clip(noisy_effect, 0.0, 1.0)

        return df

    def _date_dependence(self, df: pd.DataFrame) -> pd.DataFrame:
        """Seasonality dependence method stub.

        Args:
            df (pd.DataFrame): _description_

        Returns:
            pd.DataFrame: _description_
        """
        pass

    def _assign_sales(self, sales_df: pd.DataFrame, availability_df: pd.DataFrame) -> pd.DataFrame:
        """
        Assigns hourly 'Locale sales' to salespeople based on availability and performance weights.

        Args:
            sales_df (pd.DataFrame): Main DataFrame with columns 'timestamp' and 'Locale sales'.
            availability_df (pd.DataFrame): Combined availability with 'timestamp' and one column per
                salesperson ID (bool).

        Returns:
            pd.DataFrame: DataFrame with 'timestamp' + one column per salesperson showing assigned sales.
        """
        # Merge sales and availability on timestamp
        merged = pd.merge(sales_df[[TIMESTAMP_STR, SALES_STR]], availability_df, on=TIMESTAMP_STR, how="left")

        # Identify salesperson columns
        salespeople_ids = [col for col in merged.columns if col not in [TIMESTAMP_STR, SALES_STR]]

        # Availability matrix: shape (T, S)
        A = merged[salespeople_ids].to_numpy(dtype=float)

        # Weights vector: shape (S,)
        w = np.array([sp.performance_weight for sp in self.salespeople], dtype=float)

        # Weighted availability
        weighted_avail = A * w

        # Normalize across available salespeople, i.e. per timestamp.
        row_sums = weighted_avail.sum(axis=1, keepdims=True)
        norm_weights = np.divide(
            weighted_avail,
            row_sums,
            out=np.zeros_like(weighted_avail),
            where=row_sums != 0
        )

        # Multiply by total sales (Locale sales) and optionally Poisson draw
        total_sales = merged[SALES_STR].to_numpy().reshape(-1, 1)
        assigned_sales = np.ceil(total_sales * norm_weights).astype(np.int32)

        # Build resulting DataFrame
        assigned_df = pd.DataFrame(assigned_sales, columns=salespeople_ids)
        assigned_df.insert(0, TIMESTAMP_STR, merged[TIMESTAMP_STR])

        for sp in self.salespeople:
            sales_df = pd.DataFrame({
                TIMESTAMP_STR: assigned_df[TIMESTAMP_STR],
                SALES_STR: assigned_df[sp.person_id]
            })
            sp.assign_product_ids(sales_df, self.product_ids)

        return assigned_df