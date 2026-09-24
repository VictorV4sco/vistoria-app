from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Section:
    name: str
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    notes: str = ""
    order: int = 0
    photos: list = field(default_factory=list)
