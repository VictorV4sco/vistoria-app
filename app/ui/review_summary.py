"""Build the concise presentation of the current inspection."""

from app.models.report import Report


def review_summary(report: Report) -> dict[str, str]:
    address = ", ".join(value for value in (
        report.property.address, report.property.number, report.property.complement,
        report.property.neighborhood, report.property.city, report.property.state,
        report.property.postal_code,
    ) if value)
    return {
        "report_type": report.report_type,
        "title": report.title,
        "property": report.property.property_type,
        "address": address,
        "landlord": report.landlord.name,
        "tenant": report.tenant.name,
        "sections": str(len(report.sections)),
        "photos": str(sum(len(section.photos) for section in report.sections)),
    }
