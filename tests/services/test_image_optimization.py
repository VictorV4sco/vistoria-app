from pathlib import Path

import pytest
from PIL import Image

from app.services.image_service import ImageService


def create_original(
    project: Path, format: str = "JPEG", size: tuple[int, int] = (3200, 1600)
) -> Path:
    relative = Path("imagens/originals/photo.jpg" if format == "JPEG"
                    else "imagens/originals/photo.png")
    source = project / relative
    source.parent.mkdir(parents=True, exist_ok=True)
    mode, color = ("RGB", (120, 60, 30)) if format == "JPEG" else ("RGBA", (120, 60, 30, 80))
    Image.new(mode, size, color).save(source, format=format)
    return relative


@pytest.mark.parametrize("format", ["JPEG", "PNG"])
@pytest.mark.parametrize("size", [(3200, 1600), (1200, 2400), (400, 200)])
def test_optimization_preserves_format_proportion_and_original(
    tmp_path: Path, format: str, size: tuple[int, int]
) -> None:
    source = create_original(tmp_path, format, size)
    before = (tmp_path / source).read_bytes()

    relative = ImageService.optimize_for_report(source, tmp_path)

    assert isinstance(relative, Path)
    assert not relative.is_absolute()
    assert relative.parent == Path("imagens/optimized")
    assert relative.suffix == (".jpg" if format == "JPEG" else ".png")
    assert (tmp_path / source).read_bytes() == before
    with Image.open(tmp_path / relative) as result:
        result.load()
        scale = min(1, 1600 / max(size))
        assert result.size == (round(size[0] * scale), round(size[1] * scale))
        assert result.format == format
        if format == "PNG":
            assert result.mode == "RGBA"
            assert result.getpixel((0, 0))[3] == 80


def test_exif_orientation_is_applied_before_resizing(tmp_path: Path) -> None:
    source = create_original(tmp_path, size=(2400, 1200))
    exif = Image.Exif()
    exif[274] = 6
    with Image.new("RGB", (2400, 1200), "red") as image:
        image.paste("blue", (0, 0, 1200, 1200))
        image.save(tmp_path / source, exif=exif)
    before = (tmp_path / source).read_bytes()

    relative = ImageService.optimize_for_report(source, tmp_path)

    with Image.open(tmp_path / relative) as result:
        assert result.size == (800, 1600)
        assert result.getexif().get(274, 1) == 1
        assert result.getpixel((400, 100))[2] > 200
        assert result.getpixel((400, 1500))[0] > 200
    assert (tmp_path / source).read_bytes() == before


@pytest.mark.parametrize("invalid", [False, True])
def test_missing_or_invalid_image_raises_without_output(tmp_path: Path, invalid: bool) -> None:
    source = Path("imagens/originals/photo.jpg")
    if invalid:
        (tmp_path / source).parent.mkdir(parents=True)
        (tmp_path / source).write_bytes(b"invalid image")

    with pytest.raises(OSError if invalid else FileNotFoundError):
        ImageService.optimize_for_report(source, tmp_path)

    assert not (tmp_path / "imagens/optimized").exists()


@pytest.mark.parametrize("stage", ["save", "publish"])
def test_write_failure_leaves_no_partial_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    source = create_original(tmp_path)
    before = (tmp_path / source).read_bytes()

    def fail_save(image: Image.Image, path: Path, **kwargs: object) -> None:
        Path(path).write_bytes(b"partial")
        raise OSError("write failed")

    def fail_publish(path: Path, target: Path) -> None:
        with Image.open(path) as image:
            image.load()
        raise OSError("write failed")

    if stage == "save":
        monkeypatch.setattr(Image.Image, "save", fail_save)
    else:
        monkeypatch.setattr(Path, "replace", fail_publish)

    with pytest.raises(OSError, match="write failed"):
        ImageService.optimize_for_report(source, tmp_path)

    assert (tmp_path / source).read_bytes() == before
    assert [path for path in tmp_path.rglob("*") if path.is_file()] == [tmp_path / source]


def test_valid_cached_image_is_reused_without_resizing_or_saving(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = create_original(tmp_path)
    relative = ImageService.optimize_for_report(source, tmp_path)
    before = (tmp_path / relative).stat().st_mtime_ns

    def unexpected_processing(*args: object, **kwargs: object) -> None:
        pytest.fail("valid cached image should be reused")

    monkeypatch.setattr(Image.Image, "thumbnail", unexpected_processing)
    monkeypatch.setattr(Image.Image, "save", unexpected_processing)

    assert ImageService.optimize_for_report(source, tmp_path) == relative
    assert (tmp_path / relative).stat().st_mtime_ns == before


def test_changed_original_does_not_reuse_stale_cache(tmp_path: Path) -> None:
    source = create_original(tmp_path)
    first = ImageService.optimize_for_report(source, tmp_path)
    create_original(tmp_path, size=(200, 100))

    second = ImageService.optimize_for_report(source, tmp_path)

    assert second != first
    with Image.open(tmp_path / second) as image:
        assert image.size == (200, 100)


def test_corrupted_cache_is_regenerated(tmp_path: Path) -> None:
    source = create_original(tmp_path)
    relative = ImageService.optimize_for_report(source, tmp_path)
    (tmp_path / relative).write_bytes(b"broken cache")

    assert ImageService.optimize_for_report(source, tmp_path) == relative
    with Image.open(tmp_path / relative) as image:
        image.load()
        assert image.size == (1600, 800)


@pytest.mark.parametrize("absolute", [False, True])
def test_rejects_paths_outside_project(tmp_path: Path, absolute: bool) -> None:
    source = tmp_path / "outside.jpg" if absolute else Path("../outside.jpg")

    with pytest.raises(ValueError, match="relative|project"):
        ImageService.optimize_for_report(source, tmp_path / "project")
