"""Invalid sampling values must never reach native inference."""

import pytest
from fastapi import HTTPException

from backend.app.validation import validate_sampling_param


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), "nan", "bad"])
def test_rejects_non_finite_or_invalid_values(value):
    with pytest.raises(HTTPException) as error:
        validate_sampling_param("temperature", value, 0, 2)
    assert error.value.status_code == 422


def test_integer_parameter_does_not_silently_truncate():
    with pytest.raises(HTTPException):
        validate_sampling_param("top_k", 25.5, 1, 100, integer=True)
    assert validate_sampling_param("top_k", 25, 1, 100, integer=True) == 25


def test_optional_and_boundary_values():
    assert validate_sampling_param("top_p", None, 0, 1) is None
    assert validate_sampling_param("top_p", 1, 0, 1) == 1
    with pytest.raises(HTTPException):
        validate_sampling_param("top_p", 1.1, 0, 1)
