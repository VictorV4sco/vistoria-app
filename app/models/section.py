from dataclasses import dataclass, field
from uuid import uuid4

from app.models.photo import Photo


@dataclass
class Section:
    name: str
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    notes: str = ""
    order: int = 0
    photos: list[Photo] = field(default_factory=list)

    def add_photo(self, photo: Photo) -> None:
        self.photos.append(photo)
        self.reorder_photos()

    def remove_photo(self, photo: Photo) -> None:
        self.photos.remove(photo)

    def reorder_photos(self) -> None:
        """Sort photos by their order without changing the order values."""
        self.photos.sort(key=lambda photo: photo.order)
