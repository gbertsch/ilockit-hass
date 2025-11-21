import datetime

from custom_components.ilockit.api import ILockitApiClient


def test_parse_lock_state() -> None:
    assert ILockitApiClient._parse_lock_state(2) is True
    assert ILockitApiClient._parse_lock_state(1) is False
    assert ILockitApiClient._parse_lock_state(0) is None
    assert ILockitApiClient._parse_lock_state(None) is None


def test_parse_datetime() -> None:
    dt = ILockitApiClient._parse_datetime("2025-11-21T01:49:30.640+0000")
    assert isinstance(dt, datetime.datetime)
    assert dt.tzinfo is not None
