import pytest

from shop import InputError, half_up, parse_qty


def test_parse_qty_accepts_plain_digits():
    assert parse_qty("12") == 12


def test_parse_qty_rejects_superscript_digit():
    with pytest.raises(InputError):
        parse_qty("²")


def test_half_up_rounds_half_away_from_zero():
    assert half_up(2.5) == 3
    assert half_up(3.5) == 4
