from datetime import date

import pytest


@pytest.mark.parametrize("text, expected", [
    ("", None), ("02/10/2026", date(2026, 10, 2)), ("29/02/2024", date(2024, 2, 29)),
    ("01/01/0001", date(1, 1, 1)), ("31/02/2026", None), ("29/02/2026", None),
    ("2/10/2026", None), ("02/10/26", None), ("02/10/", None), ("texto", None),
    ("2026-10-02", None), ("00/10/2026", None), ("02/13/2026", None),
    ("02/10/0000", None), (" 02/10/2026 ", None),
])
def test_strict_date_parsing_without_exceptions(text, expected):
    from app.utils.dates import parse_date_input

    assert parse_date_input(text) == expected


@pytest.mark.parametrize("value, expected", [
    (None, ""), (date(2026, 10, 2), "02/10/2026"), (date(1, 1, 1), "01/01/0001"),
])
def test_date_input_format_is_portable(value, expected):
    from app.utils.dates import format_date_input

    assert format_date_input(value) == expected
