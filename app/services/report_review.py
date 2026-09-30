"""Read-only review checks for the MVP's Word generation flow."""

from app.models.report import Report


def missing_required_fields(report: Report) -> list[str]:
    """Return the explicit minimum fields required before generating Word."""
    required = (
        ("Tipo da vistoria", report.report_type),
        ("Título", report.title),
        ("Data da vistoria", report.inspection_date),
        ("Responsável pela vistoria", report.inspector_name),
        ("Tipo do imóvel", report.property.property_type),
        ("Endereço", report.property.address),
        ("Nome do locador", report.landlord.name),
        ("Nome do locatário", report.tenant.name),
    )
    return [label for label, value in required
            if value is None or (isinstance(value, str) and not value.strip())]


def review_warnings(report: Report) -> list[str]:
    """Return guidance that never blocks generation."""
    warnings = []
    if not report.sections:
        warnings.append("Nenhum ambiente cadastrado.")
    if not any(section.photos for section in report.sections):
        warnings.append("Nenhuma foto no relatório.")
    for section in report.sections:
        if not section.description.strip():
            warnings.append(f"{section.name}: ambiente sem descrição.")
        if not section.photos:
            warnings.append(f"{section.name}: ambiente sem fotos.")
    return warnings
