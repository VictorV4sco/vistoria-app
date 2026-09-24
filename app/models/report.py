from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import uuid4

from app.models.complementary_information import ComplementaryInformation
from app.models.party import Party
from app.models.property import Property


@dataclass
class Report:
    id: str = field(default_factory=lambda: str(uuid4()))
    version: int = 1
    sections: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
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
