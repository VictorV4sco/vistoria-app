"""Import original images into a project without modifying the user's files."""

import hashlib
import shutil
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from PIL import Image, ImageOps

# Suitable for report photos: cap the longest side without enlarging small images.
REPORT_MAX_DIMENSION = 1600
REPORT_JPEG_QUALITY = 85


class ImageService:
    """Copy and validate images before publishing them in originals."""

    @staticmethod
    def optimize_for_report(relative_path: Path, project_directory: Path) -> Path:
        """Create a report copy, preserving source bytes and PNG transparency.

        JPEG uses quality 85; the longest side is at most 1600 pixels. EXIF
        orientation is applied before resizing. Cache names hash source bytes
        and a versioned processing policy; readable cached images are reused.
        Pillow and I/O errors propagate, with temporary writes cleaned up.
        """
        project = project_directory.resolve()
        source = (project / relative_path).resolve()
        if relative_path.is_absolute() or not source.is_relative_to(project):
            raise ValueError("Image path must be relative and remain inside the project")

        content = source.read_bytes()
        policy = f"report-v1-{REPORT_MAX_DIMENSION}-{REPORT_JPEG_QUALITY}".encode()
        identifier = hashlib.sha256(policy + content).hexdigest()
        with Image.open(BytesIO(content), formats=("JPEG", "PNG")) as original:
            format = original.format
            extension = ".jpg" if format == "JPEG" else ".png"
            relative = Path("imagens/optimized") / f"{identifier}{extension}"
            destination = project / relative
            if destination.is_file():
                try:
                    with Image.open(destination) as cached:
                        cached.verify()
                    with Image.open(destination) as cached:
                        cached.load()
                        if (cached.format == format
                                and max(cached.size) <= REPORT_MAX_DIMENSION
                                and cached.getexif().get(274, 1) == 1):
                            return relative
                except (OSError, SyntaxError, ValueError):
                    # An unreadable cache is regenerated from the original.
                    pass

            original.verify()

        with Image.open(BytesIO(content), formats=("JPEG", "PNG")) as original:
            with ImageOps.exif_transpose(original) as optimized:
                optimized.thumbnail(
                    (REPORT_MAX_DIMENSION, REPORT_MAX_DIMENSION), Image.Resampling.LANCZOS
                )
                destination.parent.mkdir(parents=True, exist_ok=True)
                with TemporaryDirectory(prefix=".optimize-", dir=destination.parent) as directory:
                    temporary = Path(directory) / relative.name
                    options = {"quality": REPORT_JPEG_QUALITY} if format == "JPEG" else {}
                    optimized.save(temporary, format=format, optimize=True, **options)
                    temporary.replace(destination)

        return relative

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
