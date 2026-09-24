"""Convert reports to and from the project data format without file I/O."""

from dataclasses import asdict
from datetime import UTC, date, datetime

from app.models.complementary_information import ComplementaryInformation
from app.models.party import Party
from app.models.photo import Photo
from app.models.property import Property
from app.models.report import Report
from app.models.section import Section


def report_to_dict(report: Report) -> dict:
    """Return independent, JSON-compatible data, preserving IDs and list order.

    Photo paths are already relative to the project and are kept unchanged.
    Timestamps use UTC; naive values are rejected rather than assuming a timezone.
    """
    data = asdict(report)
    data["inspection_date"] = (
        report.inspection_date.isoformat() if report.inspection_date is not None else None
    )
    data["issue_date"] = report.issue_date.isoformat() if report.issue_date is not None else None
    for name in ("created_at", "updated_at"):
        value = getattr(report, name)
        if value.utcoffset() is None:
            raise ValueError(f"{name} must be timezone-aware")
        data[name] = value.astimezone(UTC).isoformat()
    return data


def report_from_dict(data: dict) -> Report:
    """Reconstruct a report from the complete project format without mutating data.

    This conversion preserves the stored version; it does not migrate formats.
    Timestamps must include a timezone and are restored in UTC by Report.
    """
    return Report(
        id=data["id"],
        version=data["version"],
        report_type=data["report_type"],
        title=data["title"],
        code=data["code"],
        inspection_date=(
            date.fromisoformat(data["inspection_date"])
            if data["inspection_date"] is not None
            else None
        ),
        issue_date=(
            date.fromisoformat(data["issue_date"]) if data["issue_date"] is not None else None
        ),
        inspector_name=data["inspector_name"],
        property=Property(**data["property"]),
        landlord=Party(**data["landlord"]),
        tenant=Party(**data["tenant"]),
        complementary_information=ComplementaryInformation(**data["complementary_information"]),
        sections=[
            Section(
                id=section["id"],
                name=section["name"],
                description=section["description"],
                notes=section["notes"],
                order=section["order"],
                photos=[Photo(**photo) for photo in section["photos"]],
            )
            for section in data["sections"]
        ],
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        protected_from_cleanup=data["protected_from_cleanup"],
    )
