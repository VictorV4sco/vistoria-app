from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Report:
    id: str = field(default_factory=lambda: str(uuid4()))
    version: int = 1
    sections: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)