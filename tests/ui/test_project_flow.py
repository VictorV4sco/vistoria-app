from datetime import date
from unittest.mock import Mock

import pytest
from PIL import Image
from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QPushButton

from app.models.complementary_information import ComplementaryInformation
from app.models.party import Party
from app.models.property import Property
from app.models.report import Report
from app.models.section import Section
from app.services.document_generator import DocumentGenerator
from app.services.photo_service import PhotoService
from app.services.project_service import ProjectService
from app.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    return window


@pytest.mark.parametrize("report_type", ["Inicial", "Final"])
def test_new_project_is_saved_and_bound(window, tmp_path, report_type):
    window.final_radio.setChecked(report_type == "Final")
    window.continue_button.click()
    directory = window.project_directory
    assert directory is not None
    assert directory.parent == tmp_path
    assert directory.name.startswith("vistoria-")
    assert directory.is_dir()
    assert ProjectService.load(directory) == window.report
    assert window.report.report_type == report_type
    assert window.pages.currentWidget() is window.form_page
    for page in (window.form_page, window.parties_page,
                 window.environments_page, window.review_page):
        assert page.report is window.report
    assert window.environments_page.project_directory == directory
    assert window.review_page.project_directory == directory
    assert str(directory) in window.statusBar().currentMessage()
    first = directory
    window._show_start()
    window.continue_button.click()
    assert window.project_directory != first
    assert ProjectService.load(first).report_type == report_type


@pytest.mark.parametrize("loaded", [False, True])
@pytest.mark.parametrize("action", ["new", "open"])
def test_cancel_keeps_state(window, tmp_path, monkeypatch, loaded, action):
    if loaded:
        window.continue_button.click()
        window.form_page.title_field.setText("Em edição")
        window._show_start()
    report, directory = window.report, window.project_directory
    save = Mock()
    load = Mock()
    constructor = Mock()
    monkeypatch.setattr(ProjectService, "save", save)
    monkeypatch.setattr(ProjectService, "load", load)
    monkeypatch.setattr("app.ui.main_window.Report", constructor)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: "")
    before = list(tmp_path.iterdir())
    if action == "new":
        window.continue_button.click()
    else:
        window.start_page.open_button.click()
    assert window.report is report
    assert window.project_directory == directory
    assert window.pages.currentWidget() is window.start_page
    assert list(tmp_path.iterdir()) == before
    save.assert_not_called()
    load.assert_not_called()
    constructor.assert_not_called()


@pytest.fixture
def stored_project(tmp_path):
    directory = tmp_path / "existing"
    report = Report(
        report_type="Final", title="Casa", inspection_date=date(2026, 10, 1),
        inspector_name="Ana", property=Property(property_type="Casa", address="Rua A"),
        landlord=Party(name="Locador", document="123"), tenant=Party(name="Locatário"),
        complementary_information=ComplementaryInformation("2", "123", "456", "Notas", "Rio"),
        sections=[Section("Sala", description="Pintura", notes="Observações")],
    )
    source = tmp_path / "source.png"
    Image.new("RGB", (40, 20)).save(source)
    PhotoService.import_photo(source, directory, report.sections[0], caption="Vista da sala")
    ProjectService.save(report, directory)
    return directory, report, source


def open_stored(window, monkeypatch, directory):
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(directory))
    window.start_page.open_button.click()


def test_open_preserves_everything_and_uses_loaded_object(window, stored_project, monkeypatch):
    directory, original, _ = stored_project
    loaded = ProjectService.load(directory)
    load = Mock(return_value=loaded)
    monkeypatch.setattr(ProjectService, "load", load)
    open_stored(window, monkeypatch, directory)
    load.assert_called_once_with(directory)
    assert window.report is loaded
    assert window.report == original
    assert window.project_directory == directory
    assert window.pages.currentWidget() is window.form_page
    assert window.form_page.title_field.text() == original.title
    assert window.form_page.report_type_field.text() == "Final"
    assert window.parties_page.landlord_name_field.text() == "Locador"
    assert window.review_page.general_notes_field.toPlainText() == "Notas"
    for page in (window.form_page, window.parties_page,
                 window.environments_page, window.review_page):
        assert page.report is loaded


def test_opened_photos_preview_import_move_remove(window, stored_project, monkeypatch):
    directory, original, source = stored_project
    open_stored(window, monkeypatch, directory)
    window._show_environments()
    editor = window.environments_page.editors[0]
    first = window.report.sections[0].photos[0]
    assert first.file_path == original.sections[0].photos[0].file_path
    assert not editor.photo_editors[0].preview.pixmap().isNull()
    assert editor.photo_editors[0].caption_field.text() == "Vista da sala"
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(source), ""))
    editor.add_photo_button.click()
    section = window.report.sections[0]
    second = section.photos[1]
    assert (directory / second.file_path).is_file()
    editor.photo_editors[1].up_button.click()
    assert section.photos == [second, first]
    editor.photo_editors[0].caption_field.setText("Nova legenda")
    editor.photo_editors[0].remove_button.click()
    assert section.photos == [first]


def test_save_delegates_without_recreating_objects(window, tmp_path, monkeypatch):
    window.continue_button.click()
    report = window.report
    window.form_page.title_field.setText("Editado")
    save = Mock(wraps=ProjectService.save)
    monkeypatch.setattr(ProjectService, "save", save)
    window.save_action.trigger()
    save.assert_called_once_with(report, window.project_directory)
    assert save.call_args.args[0] is report
    assert window.report is report
    assert window.form_page.report is report
    assert ProjectService.load(window.project_directory).title == "Editado"
    assert (window.project_directory / "projeto.backup.json").is_file()
    assert "salvo" in window.statusBar().currentMessage().lower()


@pytest.mark.parametrize("action", ["new", "open", "save"])
def test_errors_are_friendly_and_preserve_current_project(
    window, tmp_path, monkeypatch, action,
):
    window.continue_button.click()
    report, directory = window.report, window.project_directory
    messages = Mock()
    monkeypatch.setattr(QMessageBox, "warning", messages)
    failing = Mock(side_effect=OSError("private technical details"))
    monkeypatch.setattr(ProjectService, "load" if action == "open" else "save", failing)
    if action == "save":
        window.save_action.trigger()
    else:
        window._show_start()
        if action == "new":
            window.continue_button.click()
        else:
            window.start_page.open_button.click()
    assert window.report is report
    assert window.project_directory == directory
    messages.assert_called_once()
    message = messages.call_args.args[2]
    assert "Não foi possível" in message
    assert "Traceback" not in message
    assert "private technical details" not in message


def test_corrupt_main_does_not_recover_backup(window, stored_project, monkeypatch):
    directory, report, _ = stored_project
    ProjectService.save(report, directory)
    (directory / "projeto.json").write_text("broken", encoding="utf-8")
    messages = Mock()
    monkeypatch.setattr(QMessageBox, "warning", messages)
    open_stored(window, monkeypatch, directory)
    assert window.report is None
    assert window.project_directory is None
    assert window.pages.currentWidget() is window.start_page
    messages.assert_called_once()
    assert (directory / "projeto.json").read_text() == "broken"


def test_opened_project_generates_word(window, stored_project, monkeypatch, tmp_path):
    directory, _, _ = stored_project
    open_stored(window, monkeypatch, directory)
    window._show_review()
    destination = tmp_path / "report.docx"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(destination), ""))
    monkeypatch.setattr(QMessageBox, "information", Mock())
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    generate = Mock(wraps=DocumentGenerator.generate)
    monkeypatch.setattr(DocumentGenerator, "generate", generate)
    window.review_page.generate_button.click()
    generate.assert_called_once_with(window.report, directory, destination)
    assert destination.is_file()
    warning.assert_not_called()


def test_visible_actions_and_no_manual_directory_selection(window):
    assert window.continue_button.text() == "Nova vistoria"
    assert window.start_page.open_button.text() == "Abrir vistoria existente"
    assert window.save_action.text() == "Salvar"
    assert not window.save_action.isEnabled()
    assert all(button.text() != "Selecionar pasta do projeto"
               for button in window.environments_page.findChildren(QPushButton))
    assert all("Selecione uma pasta" not in label.text()
               for label in window.environments_page.findChildren(QLabel))


@pytest.mark.parametrize("partial", [False, True])
def test_failed_initial_save_removes_only_new_folder(window, tmp_path, monkeypatch, partial):
    window.continue_button.click()
    report, current = window.report, window.project_directory
    original_bytes = (current / "projeto.json").read_bytes()
    marker = tmp_path / "keep.txt"
    marker.write_text("Keep parent contents")
    attempted = []

    def fail_save(report, directory):
        attempted.append(directory)
        assert directory.is_dir()
        if partial:
            (directory / "projeto.tmp").write_text("partial")
            (directory / "imagens").mkdir()
            (directory / "imagens" / "partial.png").write_bytes(b"partial")
        raise OSError("initial save failed")

    monkeypatch.setattr(ProjectService, "save", fail_save)
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    window.continue_button.click()
    assert len(attempted) == 1
    assert not attempted[0].exists()
    assert set(tmp_path.glob("vistoria-*")) == {current}
    assert marker.read_text() == "Keep parent contents"
    assert (current / "projeto.json").read_bytes() == original_bytes
    assert window.report is report
    assert window.project_directory == current
    warning.assert_called_once()


def test_mkdir_collision_never_removes_existing_project(window, tmp_path, monkeypatch):
    window.continue_button.click()
    report, directory = window.report, window.project_directory
    original_bytes = (directory / "projeto.json").read_bytes()
    monkeypatch.setattr("app.ui.main_window.uuid4", lambda: Mock(hex=directory.name[9:]))
    save = Mock()
    monkeypatch.setattr(ProjectService, "save", save)
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    window.continue_button.click()
    assert (directory / "projeto.json").read_bytes() == original_bytes
    assert window.report is report
    assert window.project_directory == directory
    save.assert_not_called()
    warning.assert_called_once()


def test_cleanup_failure_keeps_original_error_handling(window, monkeypatch):
    window.continue_button.click()
    report, directory = window.report, window.project_directory
    monkeypatch.setattr(ProjectService, "save", Mock(side_effect=OSError("save failed")))
    cleanup = Mock(side_effect=OSError("cleanup failed"))
    monkeypatch.setattr("shutil.rmtree", cleanup)
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    window.continue_button.click()
    cleanup.assert_called_once()
    assert cleanup.call_args.args[0] != directory
    assert window.report is report
    assert window.project_directory == directory
    warning.assert_called_once()
    assert warning.call_args.args[1] == "Não foi possível criar a vistoria"
