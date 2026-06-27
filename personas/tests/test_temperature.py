"""
Unit tests for parse_temperature_input (models.py).

Tests run before implementation — expected RED until TEMP_MIN, TEMP_MAX, and
parse_temperature_input are added to models.py.
"""
import pytest
from models import parse_temperature_input, TEMPERATURE_MAP, TEMP_MIN, TEMP_MAX


class TestParseTemperatureInput:
    """Covers parse_temperature_input: named presets, numeric values, and error paths."""

    # Named choices resolve to correct floats
    @pytest.mark.parametrize("name,expected", [
        ("deterministic", 0.1),
        ("balanced", 0.3),
        ("creative", 0.7),
    ])
    def test_named_choices_resolve(self, name, expected):
        assert parse_temperature_input(name) == expected

    # Raw numeric strings — valid values
    @pytest.mark.parametrize("raw,expected", [
        ("0.5", 0.5),
        ("0",   0.0),
        ("2",   2.0),
        ("1.25", 1.25),
    ])
    def test_raw_numeric(self, raw, expected):
        assert parse_temperature_input(raw) == expected

    # Leading/trailing whitespace is tolerated
    def test_whitespace_stripped(self):
        assert parse_temperature_input(" 0.5 ") == 0.5

    # Out-of-range values raise ValueError; error message mentions bounds
    @pytest.mark.parametrize("raw", ["-0.1", "2.5", "3", "inf"])
    def test_out_of_range_raises(self, raw):
        with pytest.raises(ValueError) as exc_info:
            parse_temperature_input(raw)
        msg = str(exc_info.value)
        # Message must reference the valid range
        assert str(TEMP_MIN) in msg or str(TEMP_MAX) in msg or "range" in msg

    # Non-numeric junk raises ValueError; error message mentions named options
    @pytest.mark.parametrize("raw", ["hot", ""])
    def test_junk_raises(self, raw):
        with pytest.raises(ValueError) as exc_info:
            parse_temperature_input(raw)
        msg = str(exc_info.value)
        # Error must mention at least one valid preset name
        assert any(k in msg for k in TEMPERATURE_MAP.keys())

    # Error message for out-of-range explicitly mentions the upper bound
    def test_error_msg_contains_upper_bound(self):
        with pytest.raises(ValueError) as exc_info:
            parse_temperature_input("5")
        assert str(TEMP_MAX) in str(exc_info.value)

    # Error message for junk explicitly mentions named options
    def test_error_msg_contains_named_options(self):
        with pytest.raises(ValueError) as exc_info:
            parse_temperature_input("hot")
        msg = str(exc_info.value)
        assert any(k in msg for k in TEMPERATURE_MAP.keys())
