from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Photo:
    file_path: str
    id: str = field(default_factory=lambda: str(uuid4()))
    caption: str = ""
    order: int = 0
