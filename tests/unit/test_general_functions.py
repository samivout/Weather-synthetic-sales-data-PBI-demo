import pytest

from datetime import datetime, timezone, timedelta

import pandas as pd

import synda
from synda.globals import *
from synda import general_functions as gf


class TestPruneTimestamps:

    @pytest.mark.parametrize(
        "start, end, rule, expected_timestamps",
        [
            # Remove Monday-Thursday (1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday)
            (
                "2025-10-13T00:00:00",  # Monday
                "2025-10-19T00:00:00",  # Sunday
                {"days": [1, 2, 3, 4], "hours": list(range(1,24))},
                [
                    "2025-10-13T00:00:00",  # Monday (0) kept
                    "2025-10-18T00:00:00",  # Saturday (5) kept
                    "2025-10-19T00:00:00"
                ]
            ),
            # Remove hours 0-5, keep all days
            (
                "2025-10-13T00:00:00",
                "2025-10-14T06:00:00",
                {"hours": list(range(0,6))},
                [
                    # only hours >=6 remain
                    "2025-10-13T06:00:00",
                    "2025-10-13T07:00:00",
                    "2025-10-13T08:00:00",
                    "2025-10-13T09:00:00",
                    "2025-10-13T10:00:00",
                    "2025-10-13T11:00:00",
                ]
            ),
        ]
    )
    def test_prune_timestamps(self, hourly_dataframe, start, end, rule, expected_timestamps):
        df = hourly_dataframe(start, end)
        pruned = gf.prune_timestamps(
            df,
            days_to_remove=rule.get("days"),
            hours_to_remove=rule.get("hours")
        )
        
        # Convert pruned timestamps to ISO strings with timezone info
        result = pruned[TIMESTAMP_STR].dt.strftime("%Y-%m-%dT%H:%M:%S%z").tolist()
        assert result[:len(expected_timestamps)] == expected_timestamps

    def test_prune_timestamps_empty_case(self, hourly_dataframe):
        """
        Removing the only day present should result in an empty dataframe.
        """
        df = hourly_dataframe("2025-10-13T00:00:00", "2025-10-13T23:00:00")
        pruned = gf.prune_timestamps(
            df,
            days_to_remove=[0],
            hours_to_remove=None
        )

        assert pruned.empty


class TestDatetimeToISOZ:

    @pytest.mark.parametrize(
    "input_dt, expected_iso",
    [
        # Naive datetime treated as UTC
        (datetime(2025, 9, 1, 0, 0, 0), "2025-09-01T00:00:00Z"),

        # UTC-aware datetime remains unchanged
        (datetime(2025, 9, 1, 12, 30, 45, tzinfo=timezone.utc), "2025-09-01T12:30:45Z"),

        # Non-UTC timezone converted to UTC
        (datetime(2025, 9, 1, 2, 0, 0, tzinfo=timezone(timedelta(hours=2))), "2025-09-01T00:00:00Z"),  # 02:00+02:00 → 00:00 UTC
        (datetime(2025, 9, 1, 15, 15, 15, tzinfo=timezone(timedelta(hours=-4))), "2025-09-01T19:15:15Z"),  # 15:15-04:00 → 19:15 UTC
    ]
    )
    def test_datetime_to_iso_z(self, input_dt, expected_iso):
        result = gf.datetime_to_iso_z(input_dt)
        assert result == expected_iso


class TestGetInitKwargsForClass:

    def test_get_init_kwargs_for_class(self):

        class DummyClass:
            def __init__(self, a, b, c=10):
                self.a = a
                self.b = b
                self.c = c

        # Prepare a pandas Series containing extra and required columns
        data = pd.Series({
            "a": 1,
            "b": 2,
            "c": 3,
            "extra": 99
        })

        # Call the function
        kwargs = gf.get_init_kwargs_for_class(data_row=data, cls=DummyClass)

        # Check that only the required init parameters are returned
        assert set(kwargs.keys()) == {"a", "b", "c"}

        # Check that the values match
        assert kwargs["a"] == 1
        assert kwargs["b"] == 2
        assert kwargs["c"] == 3

        # Ensure extra column is ignored
        assert "extra" not in kwargs

        # Verify that the kwargs can be used to instantiate the class
        instance = DummyClass(**kwargs)
        assert instance.a == 1
        assert instance.b == 2
        assert instance.c == 3


class TestFlattenSalesAndWeatherData:

    def test_flatten_sales_and_weather_data(self):
        # Wide format: one row per timestamp, each product is a separate column
        sales_df_1 = pd.DataFrame({
            TIMESTAMP_STR: pd.to_datetime(["2025-10-01 10:00", "2025-10-01 11:00"]),
            101: [10.0, 15.0],
            102: [20.0, 25.0],
        })
        sales_df_2 = pd.DataFrame({
            TIMESTAMP_STR: pd.to_datetime(["2025-10-01 10:00"]),
            201: [15.0],
        })
        weather_df = pd.DataFrame({
            TIMESTAMP_STR: pd.to_datetime(["2025-10-01 10:00", "2025-10-01 11:00"]),
            "temperature": [18.5, 19.0],
            "humidity": [0.65, 0.60],
        })

        nested_data = {
            1: {  # location_id
                10: sales_df_1,  # salesperson 10
                11: sales_df_2,  # salesperson 11
                WTHR_OBS_STR: weather_df,
            }
        }

        sales_flat, weather_flat = gf.flatten_sales_and_weather_data(nested_data)

        # --- Assert ---

        # Check sales dataframe shape and columns
        assert not sales_flat.empty
        assert set(sales_flat.columns) == {LOC_ID_STR, PRS_ID_STR, PRD_ID_STR,
                                           TIMESTAMP_STR, SALES_STR}
        assert sales_flat[LOC_ID_STR].nunique() == 1
        assert sales_flat[PRS_ID_STR].nunique() == 2
        assert len(sales_flat) == 5  # 4 rows from sales_df_1 (2 timestamps × 2 products) + 1 row from sales_df_2

        # Check weather dataframe shape and contents
        assert not weather_flat.empty
        assert LOC_ID_STR in weather_flat.columns
        assert "temperature" in weather_flat.columns
        assert len(weather_flat) == 2  # two hourly records

        # Verify one known value
        row = sales_flat.loc[
            (sales_flat[PRS_ID_STR] == 10) &
            (sales_flat[PRD_ID_STR] == 102)
            & (sales_flat[TIMESTAMP_STR] == pd.Timestamp("2025-10-01 11:00"))
        ].iloc[0]
        assert row[SALES_STR] == 25.0


class TestUnflattenSalesAndWeatherData:

    def test_unflatten_sales_and_weather_data_roundtrip(self):
        # Wide format: one row per timestamp, each product is a separate column
        sales_df_1 = pd.DataFrame({
            TIMESTAMP_STR: pd.to_datetime(["2025-10-01 10:00", "2025-10-01 11:00"]),
            101: [10.0, 15.0],
            102: [20.0, 25.0],
        })
        sales_df_2 = pd.DataFrame({
            TIMESTAMP_STR: pd.to_datetime(["2025-10-01 10:00"]),
            201: [15.0],
        })
        weather_df = pd.DataFrame({
            TIMESTAMP_STR: pd.to_datetime(["2025-10-01 10:00", "2025-10-01 11:00"]),
            "temperature": [18.5, 19.0],
            "humidity": [0.65, 0.60],
        })

        nested_data = {
            1: {  # location_id
                10: sales_df_1,  # salesperson 10
                11: sales_df_2,  # salesperson 11
                WTHR_OBS_STR: weather_df,
            }
        }
        print("\n")
        sales_flat, weather_flat = gf.flatten_sales_and_weather_data(nested_data)
        unflattened_data = gf.unflatten_sales_and_weather_data(sales_flat, weather_flat)

        for (k_loc_0, v_loc_0), (k_loc_1, v_loc_1) in zip(sorted(nested_data.items()), sorted(unflattened_data.items())):
            for (k_pers_0, v_pers_0), (k_pers_1, v_pers_1) in zip(v_loc_0.items(), v_loc_1.items()):

                assert k_pers_0 == k_pers_1
                pd.testing.assert_frame_equal(v_pers_0, v_pers_1)


class TestSplitDatetimeRange:

    max_hours_per_range = 440

    def hours(delta: timedelta) -> float:
        return delta.total_seconds() / 3600

    def test_single_range_when_under_limit(self):
        start = datetime(2024, 1, 1, 0, 0)
        end = start + timedelta(hours=100)

        ranges = gf.split_datetime_range(start, end)

        assert len(ranges) == 1
        assert ranges[0] == (start, end)

    def test_exactly_at_limit_produces_single_range(self):
        start = datetime(2024, 1, 1, 0, 0)
        end = start + timedelta(hours=self.max_hours_per_range)

        ranges = gf.split_datetime_range(start, end)

        assert len(ranges) == 1
        assert ranges[0] == (start, end)
        assert (end - start).total_seconds() / 3600 == self.max_hours_per_range

    def test_range_is_split_when_over_limit(self):
        start = datetime(2024, 1, 1, 0, 0)
        end = start + timedelta(hours=self.max_hours_per_range + 10)

        ranges = gf.split_datetime_range(start, end)

        assert len(ranges) == 2

        first_start, first_end = ranges[0]
        second_start, second_end = ranges[1]

        assert (first_end - first_start).total_seconds() / 3600 == self.max_hours_per_range
        assert (second_end - second_start).total_seconds() / 3600 == 10

    def test_ranges_are_contiguous_and_non_overlapping(self):
        start = datetime(2024, 1, 1, 0, 0)
        end = start + timedelta(hours=1000)

        ranges = gf.split_datetime_range(start, end)

        for (prev_start, prev_end), (next_start, next_end) in zip(ranges, ranges[1:]):
            assert prev_end == next_start
            assert prev_end > prev_start
            assert next_end > next_start

    def test_ranges_fully_cover_original_interval(self):
        start = datetime(2024, 1, 1, 0, 0)
        end = start + timedelta(hours=999)

        ranges = gf.split_datetime_range(start, end)

        assert ranges[0][0] == start
        assert ranges[-1][1] == end

        total_hours = sum((r_end - r_start).total_seconds() / 3600 for r_start, r_end in ranges)
        assert total_hours == (end - start).total_seconds() / 3600

    def test_each_range_does_not_exceed_max_hours(self):
        start = datetime(2024, 1, 1, 0, 0)
        end = start + timedelta(hours=2000)

        ranges = gf.split_datetime_range(start, end)

        for r_start, r_end in ranges:
            assert (r_end - r_start).total_seconds() / 3600 <= self.max_hours_per_range

    def test_raises_when_end_equals_start(self):
        start = datetime(2024, 1, 1, 0, 0)

        with pytest.raises(ValueError):
            gf.split_datetime_range(start, start)

    def test_raises_when_end_before_start(self):
        start = datetime(2024, 1, 2, 0, 0)
        end = datetime(2024, 1, 1, 0, 0)

        with pytest.raises(ValueError):
            gf.split_datetime_range(start, end)