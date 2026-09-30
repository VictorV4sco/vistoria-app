from copy import deepcopy
from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtWidgets import QFileDialog, QMessageBox

from app.models.photo import Photo
from app.models.report import Report
from app.models.section import Section
from app.services.photo_service import PhotoService
from app.ui.environment_editor_widget import EnvironmentEditorWidget
from app.ui.environments_page import EnvironmentsPage
from app.ui.main_window import MainWindow


@pytest.fixture
def section():
    return Section("Sala")


@pytest.fixture
def editor(qtbot, section, tmp_path):
    editor = EnvironmentEditorWidget(section, project_directory=tmp_path / "project")
    qtbot.addWidget(editor)
    editor.show()
    return editor


def select_file(monkeypatch, path):
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))


def test_empty_and_missing_directory(qtbot, section, tmp_path):
    editor = EnvironmentEditorWidget(section)
    qtbot.addWidget(editor)
    editor.show()
    assert editor.photos_empty_label.isVisible()
    assert not editor.add_photo_button.isEnabled()


@pytest.mark.parametrize("extension", ["jpg", "jpeg", "png"])
def test_import_uses_service_and_preserves_source(
    editor, section, tmp_path, monkeypatch, extension,
):
    source = tmp_path / f"source.{extension}"
    Image.new("RGB", (400, 200), "red").save(source)
    original = source.read_bytes()
    select_file(monkeypatch, source)
    calls = []
    real_import = PhotoService.import_photo

    def import_photo(*args):
        calls.append(args)
        return real_import(*args)

    monkeypatch.setattr(PhotoService, "import_photo", import_photo)
    editor.add_photo_button.click()
    photo = section.photos[0]
    assert calls == [(source, editor.project_directory, section)]
    assert not Path(photo.file_path).is_absolute()
    assert (editor.project_directory / photo.file_path).read_bytes() == original
    assert source.read_bytes() == original
    assert editor.photo_editors[0].photo is photo
    pixmap = editor.photo_editors[0].preview.pixmap()
    assert not pixmap.isNull()
    assert pixmap.width() == 2 * pixmap.height()
    assert pixmap.width() <= 180
    assert not editor.photos_empty_label.isVisible()


def test_existing_photos_caption_and_remove(qtbot, tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (100, 200)).save(path)
    first = Photo("image.png", caption="Anterior")
    second = Photo("missing.jpg", order=1)
    section = Section("Sala", photos=[first, second])
    editor = EnvironmentEditorWidget(section, tmp_path)
    qtbot.addWidget(editor)
    assert [e.photo for e in editor.photo_editors] == [first, second]
    assert editor.photo_editors[0].caption_field.text() == "Anterior"
    editor.photo_editors[0].caption_field.setText("Nova legenda")
    assert section.photos[0] is first
    assert first.caption == "Nova legenda"
    assert editor.photo_editors[0].preview.pixmap().height() == 120
    editor.photo_editors[0].remove_button.click()
    assert section.photos == [second]
    assert section.photos[0] is second
    assert path.is_file()


@pytest.mark.parametrize("button, indices", [("up_button", [1, 0, 2]),
                                             ("down_button", [0, 2, 1])])
def test_move_photos(editor, section, button, indices):
    photos = [Photo(str(i), order=i * 10) for i in range(3)]
    section.photos.extend(photos)
    editor.refresh_photos()
    getattr(editor.photo_editors[1], button).click()
    for index, original in enumerate(indices):
        assert section.photos[index] is photos[original]
        assert editor.photo_editors[index].photo is photos[original]
    assert [p.order for p in section.photos] == [0, 1, 2]
    assert not editor.photo_editors[0].up_button.isEnabled()
    assert not editor.photo_editors[-1].down_button.isEnabled()
    editor.photo_editors[0].up_button.click()
    editor.photo_editors[-1].down_button.click()
    assert [p.order for p in section.photos] == [0, 1, 2]


@pytest.mark.parametrize("error", [
    ValueError("invalid"), OSError("failed"), Image.DecompressionBombError("too large"),
])
def test_import_error_does_not_mutate(editor, section, tmp_path, monkeypatch, error):
    section.photos.append(Photo("old.jpg", caption="Anterior"))
    before = deepcopy(section)
    select_file(monkeypatch, tmp_path / "invalid.jpg")
    messages = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: messages.append(args))

    def fail(*args):
        raise error

    monkeypatch.setattr(PhotoService, "import_photo", fail)
    editor.add_photo_button.click()
    assert section == before
    assert len(messages) == 1
    assert "Traceback" not in messages[0][2]


def test_cancel_dialog_changes_nothing(editor, section, monkeypatch):
    select_file(monkeypatch, "")
    editor.add_photo_button.click()
    assert section.photos == []


def test_rebinding_preserves_old_report(qtbot, tmp_path):
    old = Report(sections=[Section("Sala", photos=[Photo("old.png", caption="Antiga")])])
    before = deepcopy(old)
    page = EnvironmentsPage()
    qtbot.addWidget(page)
    page.set_report(old, tmp_path / "old")
    new = Report(sections=[Section("Quarto", photos=[Photo("new.png")])])
    page.set_report(new, tmp_path / "new")
    editor = page.editors[0]
    assert editor.project_directory == tmp_path / "new"
    editor.photo_editors[0].caption_field.setText("Nova")
    editor.photo_editors[0].remove_button.click()
    assert old == before
    assert new.sections[0].photos == []


def test_navigation_preserves_photos(qtbot, tmp_path, monkeypatch):
    window = MainWindow(project_directory=tmp_path / "project")
    qtbot.addWidget(window)
    window.continue_button.click()
    window.form_page.continue_button.click()
    window.parties_page.continue_button.click()
    page = window.environments_page
    page.add_button.click()
    source = tmp_path / "source.png"
    Image.new("RGB", (20, 10)).save(source)
    select_file(monkeypatch, source)
    page.editors[0].add_photo_button.click()
    photo = window.report.sections[0].photos[0]
    page.editors[0].photo_editors[0].caption_field.setText("Sala")
    page.back_button.click()
    window.parties_page.continue_button.click()
    page.continue_button.click()
    window.review_page.back_button.click()
    assert page.editors[0].photo_editors[0].photo is photo
    assert photo.caption == "Sala"
    assert page.editors[0].project_directory == tmp_path / "project"


def test_choose_project_directory(qtbot, tmp_path, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)
    window.continue_button.click()
    window.form_page.continue_button.click()
    window.parties_page.continue_button.click()
    page = window.environments_page
    page.add_button.click()
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(tmp_path))
    page.directory_button.click()
    assert window.project_directory == tmp_path
    assert page.editors[0].project_directory == tmp_path
    assert page.editors[0].add_photo_button.isEnabled()


def test_corrupt_image_does_not_change_section(editor, section, tmp_path, monkeypatch):
    source = tmp_path / "broken.png"
    source.write_bytes(b"not an image")
    select_file(monkeypatch, source)
    messages = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: messages.append(args))
    before = deepcopy(section)
    editor.add_photo_button.click()
    assert section == before
    assert len(messages) == 1
    assert source.read_bytes() == b"not an image"
    assert not list(editor.project_directory.rglob("*.png"))
