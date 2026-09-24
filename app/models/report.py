from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import uuid4

from app.models.complementary_information import ComplementaryInformation
from app.models.party import Party
from app.models.property import Property
from app.models.section import Section


@dataclass
class Report:
    id: str = field(default_factory=lambda: str(uuid4()))
    version: int = 1
    sections: list[Section] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    report_type: str = ""
    title: str = ""
    code: str = ""
    inspection_date: date | None = None
    issue_date: date | None = None
    inspector_name: str = ""
    property: Property = field(default_factory=Property)
    landlord: Party = field(default_factory=Party)
    tenant: Party = field(default_factory=Party)
    complementary_information: ComplementaryInformation = field(
        default_factory=ComplementaryInformation
    )
    protected_from_cleanup: bool = False

    def __post_init__(self) -> None:
        """Store aware timestamps in UTC; a missing timezone cannot be inferred."""
        for name in ("created_at", "updated_at"):
            value = getattr(self, name)
            if value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
            setattr(self, name, value.astimezone(UTC))

    def add_section(self, section: Section) -> None:
        self.sections.append(section)
        self.reorder_sections()

    def remove_section(self, section: Section) -> None:
        self.sections.remove(section)

    def reorder_sections(self) -> None:
        """Sort sections by their order without changing the order values."""
        self.sections.sort(key=lambda section: section.order)
