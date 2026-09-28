from copy import deepcopy
from pathlib import Path

import pytest
from PIL import Image

from app.models.photo import Photo
from app.models.section import Section
from app.services.image_service import ImageService
from app.services.photo_service import PhotoService


@pytest.fixture
def source(tmp_path: Path) -> Path:
    path = tmp_path / "sala.jpg"
    Image.new("RGB", (16, 16), "red").save(path)
    return path


def test_import_creates_and_adds_photo_with_relative_path_and_caption(
    tmp_path: Path, source: Path
) -> None:
    section = Section(name="Sala")
    project = tmp_path / "project"

    photo = PhotoService.import_photo(source, project, section, caption="Vista da sala")

    assert isinstance(photo, Photo)
    assert section.photos == [photo]
    assert section.photos[0] is photo
    assert photo.caption == "Vista da sala"
    assert photo.order == 0
    assert isinstance(photo.file_path, str)
    relative = Path(photo.file_path)
    assert not relative.is_absolute()
    assert relative.parent == Path("imagens/originals")
    assert (project / relative).read_bytes() == source.read_bytes()


def test_sequential_imports_have_predictable_orders(tmp_path: Path, source: Path) -> None:
    section = Section(name="Sala")

    photos = [PhotoService.import_photo(source, tmp_path / "project", section) for _ in range(3)]

    assert section.photos == photos
    assert [photo.order for photo in photos] == [0, 1, 2]
    assert all(photo.caption == "" for photo in photos)
    assert len({photo.id for photo in photos}) == 3
    assert len({photo.file_path for photo in photos}) == 3


@pytest.mark.parametrize("orders", [[0, 1, 2], [10, 20, 30], [30, 20, 10]])
def test_next_order_uses_maximum_after_removal(
    tmp_path: Path, source: Path, orders: list[int]
) -> None:
    existing = [Photo(file_path=f"imagens/{order}.jpg", order=order) for order in orders]
    section = Section(name="Sala", photos=existing.copy())
    section.remove_photo(existing[1])
    before = deepcopy(section.photos)

    photo = PhotoService.import_photo(source, tmp_path / "project", section)

    assert photo.order == max(item.order for item in before) + 1
    assert section.photos[-1] is photo
    assert section.photos[:-1] == sorted(before, key=lambda item: item.order)
    assert all(any(item is remaining for item in section.photos) for remaining in
               [existing[0], existing[2]])


def test_import_reuses_image_service_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.jpg"
    project = tmp_path / "project"
    relative = Path("imagens/originals/imported.jpg")
    calls = []

    def import_image(source_path: Path, project_directory: Path) -> Path:
        calls.append((source_path, project_directory))
        return relative

    monkeypatch.setattr(ImageService, "import_image", import_image)

    photo = PhotoService.import_photo(source, project, Section(name="Sala"))

    assert calls == [(source, project)]
    assert photo.file_path == relative.as_posix()


@pytest.mark.parametrize("has_existing_photos", [False, True])
@pytest.mark.parametrize("error", [ValueError("invalid image"), OSError("copy failed")])
def test_import_failure_does_not_change_section_or_existing_photos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    has_existing_photos: bool, error: Exception,
) -> None:
    existing = [Photo(file_path="imagens/a.jpg", caption="A", order=20),
                Photo(file_path="imagens/b.jpg", caption="B", order=10)]
    section = Section(name="Sala", photos=existing if has_existing_photos else [])
    photos_list = section.photos
    original_objects = section.photos.copy()
    before = deepcopy(section)

    def fail_import(source_path: Path, project_directory: Path) -> Path:
        raise error

    monkeypatch.setattr(ImageService, "import_image", fail_import)

    with pytest.raises(type(error), match=str(error)):
        PhotoService.import_photo(tmp_path / "source.jpg", tmp_path, section, caption="Nova")

    assert section == before
    assert section.photos is photos_list
    assert all(current is original for current, original in
               zip(section.photos, original_objects, strict=True))
