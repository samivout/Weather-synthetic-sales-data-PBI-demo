import pytest
from unittest.mock import patch

from deltalake import DeltaTable
from pathlib import Path
import pandas as pd

import synda
from synda.globals import *
from synda.data_io import DeltaWriter


class TestDeltaWriter:

    def test_delta_writer_init(self, tmp_path):

        base_path = tmp_path / "delta_tables"
        storage_opts = {"account_name": "test_account"}

        # Ensure directory does not exist before
        assert not base_path.exists()

        writer = DeltaWriter(base_path=str(base_path), storage_options=storage_opts)

        # Directory should exist following init.
        assert base_path.exists() and base_path.is_dir(), "Base directory should be created"

        assert writer.base_path == Path(base_path)
        assert writer.storage_options == storage_opts

        # Check that creating again with same path doesn't raise or re-create
        writer2 = DeltaWriter(base_path=str(base_path))
        assert writer2.base_path == Path(base_path)

        # Just to ensure no unintended files were created yet
        assert not any(base_path.iterdir()), "Base directory should be empty initially"

    @pytest.mark.parametrize("mode", ["overwrite", "append", "merge"])
    def test_delta_writer_write_table(self, tmp_path, mode, monkeypatch):
        """
        Test that DeltaWriter.write_table correctly handles overwrite, append, and merge modes.
        For 'merge', a mocked merge method is used to verify that it is called properly.
        """

        base_path = tmp_path
        writer = DeltaWriter(base_path=str(base_path))
        table_name = "weather_data"

        df_initial = pd.DataFrame({
            TIMESTAMP_STR: ["2025-09-01T00:00:00Z", "2025-09-01T01:00:00Z"],
            "temperature": [14.9, 14.1],
            "rain_accum": [0.0, 0.1],
        })

        df_new = pd.DataFrame({
            TIMESTAMP_STR: ["2025-09-01T02:00:00Z", "2025-09-01T03:00:00Z"],
            "temperature": [13.4, 13.2],
            "rain_accum": [0.0, 0.0],
        })
        
        merge_patch = patch.object(synda.data_io.DeltaWriter, synda.data_io.DeltaWriter._merge_table.__name__)

        if mode == "merge":
            # Mock the merge method, which is tested in another test.
            
            with merge_patch as mock:
                writer.write_table(df_initial, table_name, mode="merge", merge_keys=[TIMESTAMP_STR])

            mock.assert_called_once()
            return

        # Non-merge modes: write to disk
        writer.write_table(df_initial, table_name, mode="overwrite")

        # For append mode, write again
        if mode == "append":
            writer.write_table(df_new, table_name, mode="append")

        table_path = Path(writer._get_table_path(table_name))
        assert table_path.exists(), "Expected table path to exist"

        # Validate DeltaTable content
        dt = DeltaTable(str(table_path))
        df_result = dt.to_pandas().sort_values(TIMESTAMP_STR).reset_index(drop=True)

        if mode == "overwrite":
            # Should contain only initial data
            pd.testing.assert_frame_equal(df_initial, df_result)
        elif mode == "append":
            # Should contain both datasets concatenated
            expected = pd.concat([df_initial, df_new]).sort_values(TIMESTAMP_STR).reset_index(drop=True)
            pd.testing.assert_frame_equal(expected, df_result)

    @pytest.mark.parametrize("merge_keys", [[TIMESTAMP_STR]])
    def test_delta_writer_merge_table(self, tmp_path, merge_keys):

        df1 = pd.DataFrame({
        TIMESTAMP_STR: ["2025-09-01T00:00:00Z", "2025-09-01T01:00:00Z"],
        "TA_PT1H_AVG": [14.9, 14.1],
        "PRA_PT1H_ACC": [0.0, 0.0]
        })
        df2 = pd.DataFrame({
            TIMESTAMP_STR: ["2025-09-01T01:00:00Z", "2025-09-01T02:00:00Z"],
            "TA_PT1H_AVG": [15.0, 13.4],
            "PRA_PT1H_ACC": [0.0, 0.0]
        })

        table_path = f"{tmp_path}/weather_delta"
        writer = DeltaWriter(base_path=tmp_path)

        # First merge: should create new table
        writer._merge_table(df1, table_path, merge_keys)

        table = writer._get_table_path(table_path)
        dt = writer._get_table_path(table_path)

        # Read back table
        merged_df = pd.read_parquet(f"{table_path}")  # Or use deltalake.read_deltalake
        # Actually better: use deltalake.read_deltalake
        from deltalake import DeltaTable
        dt = DeltaTable(table_path)
        merged_df = dt.to_pandas()

        # Check first merge
        pd.testing.assert_frame_equal(merged_df, df1)

        # Second merge: should merge and remove duplicate timestamp
        writer._merge_table(df2, table_path, merge_keys)
        dt = DeltaTable(table_path)
        merged_df2 = dt.to_pandas()

        # Expected result: latest value for overlapping timestamp (keep last)
        expected_df = pd.DataFrame({
            TIMESTAMP_STR: ["2025-09-01T00:00:00Z", "2025-09-01T01:00:00Z", "2025-09-01T02:00:00Z"],
            "TA_PT1H_AVG": [14.9, 15.0, 13.4],
            "PRA_PT1H_ACC": [0.0, 0.0, 0.0]
        })

        pd.testing.assert_frame_equal(merged_df2, expected_df)
    
    def test_delta_writer_read_write_table_roundtrip(self, tmp_path):

        df = pd.DataFrame({
                TIMESTAMP_STR: ["2025-09-01T00:00:00Z", "2025-09-01T01:00:00Z"],
                "TA_PT1H_AVG": [14.9, 14.1],
                "PRA_PT1H_ACC": [0.0, 0.0]
                })

        writer = DeltaWriter(base_path=tmp_path)
        table_name = "weather_test"

        # Write the table
        writer.write_table(df, table_name, mode="overwrite")

        # Read it back
        read_df = writer.read_table(table_name)

        # Assert equality
        pd.testing.assert_frame_equal(read_df, df)

    def test_delta_writer_table_exists(self, tmp_path):
        
        df = pd.DataFrame({
                TIMESTAMP_STR: ["2025-09-01T00:00:00Z", "2025-09-01T01:00:00Z"],
                "TA_PT1H_AVG": [14.9, 14.1],
                "PRA_PT1H_ACC": [0.0, 0.0]
                })

        writer = DeltaWriter(base_path=tmp_path)
        table_name = "weather_check"

        # Initially, table should not exist
        assert not writer.table_exists(table_name)

        # Write the table
        writer.write_table(df, table_name, mode="overwrite")

        # Now, table should exist
        assert writer.table_exists(table_name)