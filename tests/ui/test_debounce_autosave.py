from unittest.mock import Mock

import pytest
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QInputDialog, QMessageBox

from app.services.project_service import ProjectService
from app.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.continue_button.click()
    return window


def test_timer_configuration_and_initial_clean_state(window):
    assert window.debounce_timer.interval() == 2000
    assert window.debounce_timer.isSingleShot()
    assert not window.debounce_timer.isActive()
    assert not window.autosave_service.is_dirty
    assert window.autosave_timer.interval() == 60000
    assert window.autosave_timer.isActive()


def test_changes_restart_timer(window, monkeypatch):
    start = Mock(wraps=window.debounce_timer.start)
    monkeypatch.setattr(window.debounce_timer, "start", start)
    window.form_page.title_field.setText("A")
    assert window.debounce_timer.isActive()
    window.form_page.title_field.setText("AB")
    assert start.call_count == 2
    window.form_page._update("title", "AB")
    assert start.call_count == 2


@pytest.mark.parametrize("dirty,fails", [(False, False), (True, False), (True, True)])
def test_timeout_uses_existing_save_flow(window, monkeypatch, dirty, fails):
    if dirty:
        window.form_page.title_field.setText("Editado")
    save = Mock(side_effect=OSError("disk") if fails else None)
    warning = Mock()
    monkeypatch.setattr(ProjectService, "save", save)
    monkeypatch.setattr(QMessageBox, "warning", warning)
    # Simulate single-shot delivery without waiting for wall-clock time.
    window.debounce_timer.stop()
    window.debounce_timer.timeout.emit()
    assert save.call_count == int(dirty)
    if dirty:
        save.assert_called_once_with(window.report, window.project_directory)
        assert window.statusBar().currentMessage() == (
            "Falha ao salvar automaticamente" if fails else "Salvo automaticamente"
        )
    assert window.autosave_service.is_dirty == fails
    warning.assert_not_called()


@pytest.mark.parametrize("save_method", ["_save_project", "_save_checkpoint", "_autosave_tick"])
def test_save_cancels_pending_debounce(window, monkeypatch, save_method):
    window.form_page.title_field.setText("Editado")
    assert window.debounce_timer.isActive()
    save = Mock(wraps=ProjectService.save)
    monkeypatch.setattr(ProjectService, "save", save)
    getattr(window, save_method)()
    assert not window.debounce_timer.isActive()
    assert not window.autosave_service.is_dirty
    window.debounce_timer.timeout.emit()
    save.assert_called_once()


def test_bindings_do_not_start_debounce(window):
    report, directory = window.report, window.project_directory
    window.form_page.set_report(report)
    window.parties_page.set_report(report)
    window.environments_page.set_report(report, directory)
    window.review_page.set_report(report, directory)
    assert not window.debounce_timer.isActive()


@pytest.mark.parametrize("action", ["new", "open", "backup"])
def test_project_replacement_cancels_old_debounce(window, monkeypatch, action):
    window.form_page.title_field.setText("Salvo")
    window._save_project()
    window.form_page.title_field.setText("Pendente")
    assert window.debounce_timer.isActive()

    def question(*args):
        assert not window.debounce_timer.isActive()
        return (QMessageBox.StandardButton.Discard if args[1] == "Alterações não salvas"
                else QMessageBox.StandardButton.Yes)

    monkeypatch.setattr(QMessageBox, "question", question)
    if action == "open":
        monkeypatch.setattr(QInputDialog, "getItem", lambda *args: (args[3][0], True))
    {"new": window._start_inspection, "open": window._open_project,
     "backup": window._recover_backup}[action]()
    assert not window.debounce_timer.isActive()
    assert not window.autosave_service.is_dirty
    assert window.autosave_timer.isActive()


@pytest.mark.parametrize("cancel", [False, True])
def test_close_cancels_timer_only_when_accepted(window, monkeypatch, cancel):
    window.form_page.title_field.setText("Pendente")

    def question(*args):
        assert not window.debounce_timer.isActive()
        return QMessageBox.StandardButton.Cancel if cancel else QMessageBox.StandardButton.Discard

    monkeypatch.setattr(QMessageBox, "question", question)
    event = QCloseEvent()
    window.closeEvent(event)
    assert event.isAccepted() == (not cancel)
    assert window.debounce_timer.isActive() == cancel
    if not cancel:
        assert not window.autosave_timer.isActive()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Discard)


def test_cancelled_switch_keeps_pending_changes_and_debounce(window, monkeypatch):
    window.form_page.title_field.setText("Pendente")
    report = window.report
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel)
    window._start_inspection()
    assert window.report is report
    assert window.autosave_service.is_dirty
    assert window.debounce_timer.isActive()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Discard)
