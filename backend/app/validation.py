"""Validation shared by short-form, clone, and long-form synthesis."""

import math

from fastapi import HTTPException


def validate_sampling_param(name, value, minimum, maximum, integer=False):
    """Reject non-finite and fractional integer values before model inference."""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid {name}") from exc
    if not math.isfinite(number):
        raise HTTPException(status_code=422, detail=f"Invalid {name}")
    if integer and not number.is_integer():
        raise HTTPException(status_code=422, detail=f"Invalid {name}")
    if not minimum <= number <= maximum:
        raise HTTPException(status_code=422, detail=f"{name} out of range")
    return int(number) if integer else number
