"""Coordinate image imports and their association with domain sections."""

from pathlib import Path

from app.models.photo import Photo
from app.models.section import Section
from app.services.image_service import ImageService


class PhotoService:
    """Associate imported images with sections without filesystem logic in models."""

    @staticmethod
    def import_photo(
        source_path: Path,
        project_directory: Path,
        section: Section,
        caption: str = "",
    ) -> Photo:
        """Import and append a photo, leaving the section unchanged on import failure.

        Order starts at zero for an empty section, otherwise at the greatest
        existing order plus one. Existing photos keep their order values.
        """
        relative_path = ImageService.import_image(source_path, project_directory)
        photo = Photo(
            file_path=relative_path.as_posix(),
            caption=caption,
            order=max((existing.order for existing in section.photos), default=-1) + 1,
        )
        section.add_photo(photo)
        return photo
