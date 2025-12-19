"""
Module for mock fixtures to provide static mocks for various package objects.
"""
import pytest
from unittest.mock import MagicMock, create_autospec

import pandas as pd

from synda.globals import *
from synda.models.salesperson_model import SimpleSalespersonModel
from synda.config import Config


@pytest.fixture
def mock_config() -> MagicMock:
    """Utility fixture for getting a mocked config instance.

    Returns:
        MagicMock: a MagicMock instance for mocking Config class.
    """
    mock_instance = MagicMock()
    mock_instance.get_location_id.return_value = "Helsinki"
    mock_instance.get_stored_query_id.return_value = "dummy_stored_query_id"

    mock_instance._locations = pd.DataFrame([
        {LOC_ID_STR: 1, "Name": "Loc1"},
        {LOC_ID_STR: 2, "Name": "Loc2"}
    ])

    mock_instance._salespeople = pd.DataFrame({
        PRS_ID_STR: [101, 102, 103],
        LOC_ID_STR: [1, 1, 2],
        "Other": ["a", "b", "c"]
    })

    return mock_instance


@pytest.fixture
def mock_weather_model() -> MagicMock:
    
    mock_instance = MagicMock()

    return mock_instance


@pytest.fixture
def mock_salesperson_model() -> MagicMock:

    mock_instance = MagicMock()

    return mock_instance


@pytest.fixture
def mock_locale_model() -> MagicMock:

    mock_instance = MagicMock()
    mock_instance.location_id = 1
    mock_instance.get_sales_data.return_value = (mock_instance.location_id, "dummy")

    return mock_instance


@pytest.fixture
def simple_salesperson_factory():
    """
    Factory fixture that returns autospecced SimpleSalespersonModel instances.

    The returned factory function accepts the same init args as SimpleSalespersonModel,
    with defaults that can be overridden via keyword arguments.
    """

    def _factory(**overrides):
        # Default values (these are sensible placeholders for tests)
        defaults = {
            "person_id": 1,
            "performance_weight": 1.0,
            "config": create_autospec(Config, instance=True),  # mock config dependency
            "inject_noise": False,
            "working_hours": (9, 17),
        }

        # Merge defaults and overrides
        params = {**defaults, **overrides}

        # Create an autospecced instance of SimpleSalespersonModel
        mock_instance = create_autospec(
            SimpleSalespersonModel,
            instance=True,
            spec_set=False,
            **params
        )

        # Allow setting or overriding attributes manually if necessary
        for key, value in params.items():
            setattr(mock_instance, key, value)

        return mock_instance

    return _factory