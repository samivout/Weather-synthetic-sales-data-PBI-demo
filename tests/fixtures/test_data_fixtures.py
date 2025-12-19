"""
Module for test data fixtures used in tests.
"""
import pytest

from pathlib import Path

sample_file_directory = Path(__file__).parent.parent / "test_data"


@pytest.fixture
def sample_fmi_xml() -> Path:

    file_path = sample_file_directory / "fmi_xml_sample.xml"
    return file_path


@pytest.fixture
def sample_location_csv() -> Path:

    file_path = sample_file_directory / "location_config.csv"
    return file_path


@pytest.fixture
def sample_salespeople_csv() -> Path:

    file_path = sample_file_directory / "salespeople_config.csv"
    return file_path


@pytest.fixture
def sample_products_csv() -> Path:

    file_path = sample_file_directory / "product_config.csv"
    return file_path


@pytest.fixture
def sample_product_locations_csv() -> Path:

    file_path = sample_file_directory / "product_location_config.csv"
    return file_path

@pytest.fixture
def sample_delta_root() -> Path:

    file_path = sample_file_directory / "delta"
    return file_path