"""Import original images into a project without modifying the user's files."""

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from PIL import Image


class ImageService:
    """Copy and validate images before publishing them in originals."""

    @staticmethod
    def import_image(source_path: Path, project_directory: Path) -> Path:
        """Return a relative Path, normalizing JPEG to .jpg and PNG to .png.

        Extension/format mismatches raise ValueError. Pillow validation errors
        and filesystem errors propagate. Only the temporary copy is moved;
        the source is never modified. Temporary files are cleaned on failure.
        """
        formats = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG"}
        expected_format = formats.get(source_path.suffix.lower())
        if expected_format is None:
            raise ValueError("Unsupported image extension; expected JPG, JPEG or PNG")

        extension = ".jpg" if expected_format == "JPEG" else ".png"
        relative = Path("imagens") / "originals" / f"{uuid4()}{extension}"
        images = project_directory / "imagens"
        images.mkdir(parents=True, exist_ok=True)

        with TemporaryDirectory(prefix=".import-", dir=images) as temporary_directory:
            temporary = Path(temporary_directory) / relative.name
            shutil.copyfile(source_path, temporary)
            with Image.open(temporary) as image:
                if image.format != expected_format:
                    raise ValueError("Image content does not match its extension")
                image.verify()
            # verify checks structure; load also detects incomplete pixel data.
            with Image.open(temporary) as image:
                image.load()

            destination = project_directory / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary.replace(destination)

        return relative
