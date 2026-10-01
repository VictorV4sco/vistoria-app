from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QMessageBox

from app.services.app_paths import AppPaths
from app.services.cleanup_service import CleanupResult, CleanupService
from app.ui.main_window import MainWindow


@pytest.fixture
def dialogs(monkeypatch):
    mocks = [Mock(), Mock()]
    monkeypatch.setattr(QMessageBox, "information", mocks[0])
    monkeypatch.setattr(QMessageBox, "warning", mocks[1])
    return mocks


def test_deferred_once_and_current_project(qtbot, tmp_path, monkeypatch, dialogs):
    paths = AppPaths(tmp_path / "app")
    current = paths.projects_root / "current"
    run = Mock(return_value=CleanupResult())
    monkeypatch.setattr(CleanupService, "run", run)
    window = MainWindow(current, app_paths=paths)
    qtbot.addWidget(window)
    run.assert_not_called()
    QCoreApplication.processEvents()
    run.assert_called_once_with(paths, current_project=current)
    window._run_automatic_cleanup()
    QCoreApplication.processEvents()
    run.assert_called_once()
    for dialog in dialogs:
        dialog.assert_not_called()
    assert window.statusBar().currentMessage() == ""


def test_normal_start_and_project_navigation_do_not_repeat(qtbot, monkeypatch, dialogs):
    run = Mock(return_value=CleanupResult())
    monkeypatch.setattr(CleanupService, "run", run)
    window = MainWindow()
    qtbot.addWidget(window)
    QCoreApplication.processEvents()
    run.assert_called_once_with(window.app_paths, current_project=None)
    window.continue_button.click()
    window._show_start()
    window._show_form()
    window._show_parties()
    window._show_environments()
    window._show_review()
    window._save_project()
    window._open_project()
    QCoreApplication.processEvents()
    run.assert_called_once()


@pytest.mark.parametrize("dirty", [False, True])
def test_automatic_cleanup_preserves_state(qtbot, monkeypatch, dirty):
    run = Mock(return_value=CleanupResult())
    monkeypatch.setattr(CleanupService, "run", run)
    window = MainWindow()
    qtbot.addWidget(window)
    window.continue_button.click()
    if dirty:
        window.form_page.title_field.setText("Editado")
    report, directory, autosave = window.report, window.project_directory, window.autosave_service
    debounce_active = window.debounce_timer.isActive()
    QCoreApplication.processEvents()
    run.assert_called_once_with(window.app_paths, current_project=directory)
    assert window.report is report
    assert window.project_directory == directory
    assert window.autosave_service is autosave
    assert autosave.is_dirty == dirty
    assert window.autosave_timer.isActive()
    assert window.debounce_timer.isActive() == debounce_active


def test_structural_error_is_generic_and_window_remains_usable(qtbot, monkeypatch, dialogs):
    run = Mock(side_effect=PermissionError("private path /secret/customer"))
    monkeypatch.setattr(CleanupService, "run", run)
    window = MainWindow()
    qtbot.addWidget(window)
    QCoreApplication.processEvents()
    assert window.statusBar().currentMessage() == "Não foi possível executar a limpeza automática"
    for dialog in dialogs:
        dialog.assert_not_called()
    window.continue_button.click()
    assert window.report is not None
    assert window.autosave_timer.isActive()
    window._run_automatic_cleanup()
    run.assert_called_once()


def test_result_summary_has_counts_without_private_details(qtbot, tmp_path, monkeypatch, dialogs):
    private = tmp_path / "private-customer"
    result = CleanupResult(moved_to_trash=[private, private], deleted=[private],
                           errors={private: "private error"})
    monkeypatch.setattr(CleanupService, "run", Mock(return_value=result))
    window = MainWindow()
    qtbot.addWidget(window)
    QCoreApplication.processEvents()
    text = window.statusBar().currentMessage()
    assert "2 movidos" in text and "1 excluído" in text
    assert "erro" in text.lower()
    assert str(tmp_path) not in text and "private" not in text
    for dialog in dialogs:
        dialog.assert_not_called()


def test_manual_still_shows_summary_and_does_not_repeat_auto(qtbot, monkeypatch, dialogs):
    run = Mock(return_value=CleanupResult())
    monkeypatch.setattr(CleanupService, "run", run)
    window = MainWindow()
    qtbot.addWidget(window)
    QCoreApplication.processEvents()
    assert run.call_count == 1
    window.cleanup_action.trigger()
    assert run.call_count == 2
    dialogs[0].assert_called_once()
    assert "Limpeza concluída" in dialogs[0].call_args.args[2]
    QCoreApplication.processEvents()
    window._run_automatic_cleanup()
    assert run.call_count == 2


def test_each_window_has_its_own_single_execution(qtbot, monkeypatch):
    run = Mock(return_value=CleanupResult())
    monkeypatch.setattr(CleanupService, "run", run)
    first, second = MainWindow(), MainWindow()
    qtbot.addWidget(first)
    qtbot.addWidget(second)
    QCoreApplication.processEvents()
    assert run.call_count == 2
    first._run_automatic_cleanup()
    second._run_automatic_cleanup()
    QCoreApplication.processEvents()
    assert run.call_count == 2
