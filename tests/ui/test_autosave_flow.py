from unittest.mock import Mock

import pytest
from PIL import Image
from PySide6.QtCore import QDate
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QFileDialog, QMessageBox

from app.models.report import Report
from app.services.document_generator import DocumentGenerator
from app.services.project_service import ProjectService
from app.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.continue_button.click()
    window.autosave_timer.stop()
    return window


@pytest.mark.parametrize("page,field,value", [
    ("form_page", "title_field", "Título"), ("form_page", "code_field", "ABC"),
    ("form_page", "inspector_name_field", "Ana"),
    *[("form_page", f"{name}_field", "Novo") for name in
      ("address", "number", "complement", "neighborhood", "city", "state", "postal_code")],
    *[("parties_page", f"{role}_{name}_field", "Novo") for role in ("landlord", "tenant")
      for name in ("name", "document", "phone", "email", "address")],
    *[("review_page", f"{name}_field", "Novo") for name in
      ("delivered_keys", "energy_meter", "consumer_unit", "issue_location")],
])
def test_text_changes_mark_dirty(window, page, field, value):
    assert not window.autosave_service.is_dirty
    getattr(getattr(window, page), field).setText(value)
    assert window.autosave_service.is_dirty
    assert window.statusBar().currentMessage() == "Alterações não salvas"


@pytest.mark.parametrize("field", ["inspection_date_field", "issue_date_field"])
def test_dates_mark_dirty(window, field):
    getattr(window.form_page, field).setDate(QDate(2026, 10, 1))
    assert window.autosave_service.is_dirty


def test_property_type_and_multiline_changes(window):
    window.form_page.property_type_field.setCurrentText("Casa")
    assert window.autosave_service.is_dirty
    window._save_project()
    window.form_page.description_field.setPlainText("Descrição")
    assert window.autosave_service.is_dirty
    window._save_project()
    window.review_page.general_notes_field.setPlainText("Notas")
    assert window.autosave_service.is_dirty


def test_loading_and_unchanged_values_are_clean(window, monkeypatch):
    window.form_page.title_field.setText("Título")
    window._save_project()
    report = window.report
    window.form_page.set_report(report)
    window.parties_page.set_report(report)
    window.environments_page.set_report(report, window.project_directory)
    window.review_page.set_report(report, window.project_directory)
    window.form_page._update("title", "Título")
    assert not window.autosave_service.is_dirty
    directory = window.project_directory
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(directory))
    window._open_project()
    assert not window.autosave_service.is_dirty


def test_environment_changes(window):
    page = window.environments_page
    page.add_button.click()
    assert window.autosave_service.is_dirty
    for name in ("name", "description", "notes"):
        window._save_project()
        field = getattr(page.editors[0], f"{name}_field")
        (field.setText if name == "name" else field.setPlainText)("Novo")
        assert window.autosave_service.is_dirty
    page.add_button.click()
    window._save_project()
    page.editors[1].up_button.click()
    assert window.autosave_service.is_dirty
    window._save_project()
    page.editors[0].remove_button.click()
    assert window.autosave_service.is_dirty
    window._save_project()
    page._move(window.report.sections[0], -1)
    assert not window.autosave_service.is_dirty


def test_photo_changes(window, tmp_path, monkeypatch):
    page = window.environments_page
    page.add_button.click()
    source = tmp_path / "source.png"
    Image.new("RGB", (20, 10)).save(source)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(source), ""))
    editor = page.editors[0]
    for _ in range(2):
        window._save_project()
        editor.add_photo_button.click()
        assert window.autosave_service.is_dirty
    window._save_project()
    editor.photo_editors[0].caption_field.setText("Legenda")
    assert window.autosave_service.is_dirty
    window._save_project()
    editor.photo_editors[1].up_button.click()
    assert window.autosave_service.is_dirty
    window._save_project()
    editor.photo_editors[0].remove_button.click()
    assert window.autosave_service.is_dirty
    window._save_project()
    editor.photos_widget._move(window.report.sections[0].photos[0], -1)
    assert not window.autosave_service.is_dirty


@pytest.mark.parametrize("automatic", [False, True])
@pytest.mark.parametrize("fails", [False, True])
def test_save_state_and_errors(window, monkeypatch, automatic, fails):
    report = window.report
    window.form_page.title_field.setText("Editado")
    save = Mock(side_effect=OSError("disk") if fails else None)
    warning = Mock()
    monkeypatch.setattr(ProjectService, "save", save)
    monkeypatch.setattr(QMessageBox, "warning", warning)
    (window._autosave_tick if automatic else window._save_project)()
    save.assert_called_once_with(report, window.project_directory)
    assert window.report is report
    assert window.autosave_service.is_dirty == fails
    assert warning.call_count == int(fails and not automatic)
    if automatic:
        assert window.statusBar().currentMessage() == (
            "Falha ao salvar automaticamente" if fails else "Salvo automaticamente"
        )


def test_clean_tick_and_missing_project_do_not_save(window, monkeypatch):
    save = Mock()
    monkeypatch.setattr(ProjectService, "save", save)
    assert window.autosave_timer.interval() == 60000
    window._autosave_tick()
    window.report = None
    window._autosave_tick()
    save.assert_not_called()


@pytest.mark.parametrize("action", ["new", "open", "close"])
@pytest.mark.parametrize("choice,fails", [("Cancel", False), ("Discard", False),
                                         ("Save", False), ("Save", True)])
def test_dirty_protection(window, tmp_path, monkeypatch, action, choice, fails):
    target = tmp_path / "other"
    ProjectService.save(Report(title="Outro"), target)
    report, directory = window.report, window.project_directory
    window.form_page.title_field.setText("Editado")
    question = Mock(return_value=getattr(QMessageBox.StandardButton, choice))
    folder = Mock(return_value=str(target if action == "open" else tmp_path))
    save = Mock(wraps=ProjectService.save) if not fails else Mock(side_effect=OSError("disk"))
    monkeypatch.setattr(QMessageBox, "question", question)
    monkeypatch.setattr(QMessageBox, "warning", Mock())
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", folder)
    monkeypatch.setattr(ProjectService, "save", save)
    event = QCloseEvent()
    if action == "close":
        window.closeEvent(event)
    else:
        (window._start_inspection if action == "new" else window._open_project)()
    question.assert_called_once()
    aborted = choice == "Cancel" or fails
    if action == "close":
        assert event.isAccepted() == (not aborted)
        folder.assert_not_called()
    elif aborted:
        folder.assert_not_called()
    else:
        folder.assert_called_once()
        assert window.report is not report
        assert not window.autosave_service.is_dirty
    if aborted or action == "close":
        assert window.report is report
        assert window.project_directory == directory
    if choice == "Save":
        assert save.call_args_list[0].args == (report, directory)
    elif action != "new" or aborted:
        save.assert_not_called()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Discard)


def test_clean_close_does_not_ask(window, monkeypatch):
    question = Mock()
    monkeypatch.setattr(QMessageBox, "question", question)
    event = QCloseEvent()
    window.closeEvent(event)
    assert event.isAccepted()
    question.assert_not_called()


@pytest.mark.parametrize("fails", [False, True])
def test_review_checkpoint(window, monkeypatch, fails):
    window._show_environments()
    window.environments_page.add_button.click()
    monkeypatch.setattr(ProjectService, "save", Mock(side_effect=OSError() if fails else None))
    monkeypatch.setattr(QMessageBox, "warning", Mock())
    window.environments_page.continue_button.click()
    assert window.pages.currentWidget() is (
        window.environments_page if fails else window.review_page
    )
    assert window.autosave_service.is_dirty == fails


@pytest.mark.parametrize("fails", [False, True])
def test_word_saves_before_generation(window, tmp_path, monkeypatch, fails):
    report = window.report
    report.title = "Casa"
    report.inspection_date = QDate(2026, 10, 1).toPython()
    report.inspector_name = "Ana"
    report.property.property_type = "Casa"
    report.property.address = "Rua"
    report.landlord.name = "A"
    report.tenant.name = "B"
    window._show_review()
    window.review_page.delivered_keys_field.setText("2")
    calls = []

    def save(*args):
        calls.append("save")
        if fails:
            raise OSError("disk")

    generate = Mock(side_effect=lambda *args: calls.append("generate"))
    monkeypatch.setattr(ProjectService, "save", save)
    monkeypatch.setattr(DocumentGenerator, "generate", generate)
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(tmp_path / "a.docx"), "")
    )
    monkeypatch.setattr(QMessageBox, "warning", Mock())
    monkeypatch.setattr(QMessageBox, "information", Mock())
    window.review_page.generate_button.click()
    assert calls == (["save"] if fails else ["save", "generate"])
    assert window.autosave_service.is_dirty == fails


@pytest.mark.parametrize("action", ["new", "open"])
def test_clean_project_switch_does_not_ask(window, tmp_path, monkeypatch, action):
    directory = window.project_directory
    question = Mock()
    monkeypatch.setattr(QMessageBox, "question", question)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(
        directory if action == "open" else tmp_path
    ))
    (window._start_inspection if action == "new" else window._open_project)()
    question.assert_not_called()
    assert not window.autosave_service.is_dirty


def test_cancelled_and_failed_photo_import_stay_clean(window, monkeypatch):
    window.environments_page.add_button.click()
    window._save_project()
    button = window.environments_page.editors[0].add_photo_button
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: ("", ""))
    button.click()
    assert not window.autosave_service.is_dirty
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: ("missing.png", ""))
    monkeypatch.setattr(QMessageBox, "warning", Mock())
    button.click()
    assert not window.autosave_service.is_dirty


def test_loading_preserves_pending_changes(window):
    window.form_page.title_field.setText("Editado")
    window.form_page.set_report(window.report)
    window.parties_page.set_report(window.report)
    window.environments_page.set_report(window.report, window.project_directory)
    window.review_page.set_report(window.report, window.project_directory)
    assert window.autosave_service.is_dirty
