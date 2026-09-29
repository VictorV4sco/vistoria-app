"""Portuguese date formatting independent of operating-system locale."""

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
