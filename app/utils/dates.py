"""Portuguese date formatting independent of operating-system locale."""

import re
from datetime import date

MONTHS_PT_BR = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


def format_date_pt_br(value: date | None) -> str:
    """Return a date in full Portuguese, or empty text when absent."""
    if value is None:
        return ""
    return f"{value.day} de {MONTHS_PT_BR[value.month - 1]} de {value.year}"


def parse_date_input(text: str) -> date | None:
    """Parse strict DD/MM/YYYY; empty or invalid input returns None without raising."""
    if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", text):
        return None
    day, month, year = (int(part) for part in text.split("/"))
    try:
        return date(year, month, day)
    except ValueError:
        return None


def format_date_input(value: date | None) -> str:
    """Format editable dates with four year digits on every operating system."""
    return f"{value.day:02d}/{value.month:02d}/{value.year:04d}" if value is not None else ""
