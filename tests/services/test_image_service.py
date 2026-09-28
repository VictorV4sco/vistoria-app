import shutil
from pathlib import Path
from uuid import UUID

import pytest
from PIL import Image

from app.services.image_service import ImageService


@pytest.mark.parametrize(
    ("extension", "format", "expected"),
    [(".jpg", "JPEG", ".jpg"), (".jpeg", "JPEG", ".jpg"),
     (".png", "PNG", ".png"), (".JPG", "JPEG", ".jpg"),
     (".JPEG", "JPEG", ".jpg"), (".PNG", "PNG", ".png")],
)
def test_import_copies_valid_image_to_relative_uuid_path(
    tmp_path: Path, extension: str, format: str, expected: str
) -> None:
    source = tmp_path / f"photo{extension}"
    Image.new("RGB", (16, 16), "red").save(source, format=format)
    original = source.read_bytes()
    modified = source.stat().st_mtime_ns
    project = tmp_path / "project"

    relative = ImageService.import_image(source, project)

    assert isinstance(relative, Path)
    assert not relative.is_absolute()
    assert relative.parent == Path("imagens/originals")
    assert relative.suffix == expected
    assert UUID(relative.stem).version == 4
    assert source.read_bytes() == original
    assert source.stat().st_mtime_ns == modified
    assert (project / relative).read_bytes() == original
    assert list((project / relative.parent).iterdir()) == [project / relative]
    source.unlink()
    with Image.open(project / relative) as image:
        image.load()
        assert image.format == format


@pytest.mark.parametrize("extension", [".gif", ".bmp", ".txt", ""])
def test_rejects_unsupported_extension(tmp_path: Path, extension: str) -> None:
    source = tmp_path / f"photo{extension}"
    Image.new("RGB", (16, 16)).save(source, format="PNG")
    project = tmp_path / "project"

    with pytest.raises(ValueError):
        ImageService.import_image(source, project)

    assert not list(project.rglob("*.*"))


@pytest.mark.parametrize("kind", ["garbage", "truncated", "disguised", "mismatch"])
def test_rejects_invalid_image_without_leaving_files(tmp_path: Path, kind: str) -> None:
    source = tmp_path / "photo.jpg"
    Image.new("RGB", (16, 16)).save(source, format="JPEG")
    if kind == "garbage":
        source.write_bytes(b"not an image")
    elif kind == "truncated":
        source.write_bytes(source.read_bytes()[:-20])
    elif kind == "disguised":
        Image.new("RGB", (16, 16)).save(source, format="GIF")
    else:
        Image.new("RGB", (16, 16)).save(source, format="PNG")
    original = source.read_bytes()
    project = tmp_path / "project"

    with pytest.raises((ValueError, OSError)):
        ImageService.import_image(source, project)

    assert not [path for path in project.rglob("*") if path.is_file()]
    assert source.read_bytes() == original


def test_same_names_generate_unique_copies(tmp_path: Path) -> None:
    project = tmp_path / "project"
    paths = []
    for name, color in [("a", "red"), ("b", "blue")]:
        directory = tmp_path / name
        directory.mkdir()
        source = directory / "photo.jpg"
        Image.new("RGB", (16, 16), color).save(source)
        relative = ImageService.import_image(source, project)
        paths.append(relative)
        assert (project / relative).read_bytes() == source.read_bytes()

    assert paths[0] != paths[1]
    assert len(list((project / "imagens/originals").iterdir())) == 2


@pytest.mark.parametrize("stage", ["copy", "publish"])
def test_io_failure_leaves_no_partial_image_and_preserves_existing_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    source = tmp_path / "photo.jpg"
    Image.new("RGB", (16, 16)).save(source)
    original = source.read_bytes()
    project = tmp_path / "project"
    previous = ImageService.import_image(source, project)

    def fail_copy(source: Path, destination: Path) -> None:
        destination.write_bytes(b"partial")
        raise OSError("copy failed")

    def fail_replace(source: Path, destination: Path) -> None:
        assert source.read_bytes() == original
        raise OSError("publish failed")

    if stage == "copy":
        monkeypatch.setattr(shutil, "copyfile", fail_copy)
    else:
        monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(OSError, match=f"{stage} failed"):
        ImageService.import_image(source, project)

    assert source.read_bytes() == original
    assert (project / previous).read_bytes() == original
    assert [path for path in project.rglob("*") if path.is_file()] == [project / previous]


def test_missing_source_propagates_error_without_leaving_files(tmp_path: Path) -> None:
    project = tmp_path / "project"

    with pytest.raises(FileNotFoundError):
        ImageService.import_image(tmp_path / "missing.jpg", project)

    assert not [path for path in project.rglob("*") if path.is_file()]
