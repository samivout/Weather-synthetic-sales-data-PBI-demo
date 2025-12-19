import pytest
from unittest.mock import MagicMock, patch

import pandas as pd

import synda
from synda.globals import *
from synda.fetch_data import parse_fmi_xml, fetch_data_wfs


class TestParseFmiXml:

    def test_parse_fmi_xml_success(self, sample_fmi_xml):
        # Expect this test to break if the sample_fmi_xml data is modified.
        expected_df = pd.DataFrame({
            TIMESTAMP_STR: [
                "2025-07-01T12:00:00Z",
                "2025-07-01T13:00:00Z",
                "2025-07-01T14:00:00Z",
                "2025-07-01T15:00:00Z",
                "2025-07-01T16:00:00Z",
            ],
            "TA_PT1H_AVG": [24.6, 24.5, 24.6, 24.8, 24.4],
            "PRA_PT1H_ACC": [0.0, 0.0, 0.0, 0.0, 0.0]
        })
        expected_df[TIMESTAMP_STR] = pd.to_datetime(expected_df[TIMESTAMP_STR], utc=True)

        sample_xml_bytes = sample_fmi_xml.read_bytes()
        parsed_df = parse_fmi_xml(sample_xml_bytes)

        pd.testing.assert_frame_equal(expected_df, parsed_df)


class TestFetchDataWfs:

    def test_fetch_data_wfs_success(self):
        
        mock_wfs = MagicMock()
        mock_response = MagicMock()
        mock_response.read.return_value = "dummy"
        mock_wfs.getfeature.return_value = mock_response
        wfs_patch = patch.object(synda.fetch_data, synda.fetch_data.WebFeatureService.__name__, return_value=mock_wfs)

        with wfs_patch:

            ret = fetch_data_wfs("mock.url", "2.0.0", stored_query_id="mock_query", query_params={"mock": "val"})
        
        assert ret == "dummy"


