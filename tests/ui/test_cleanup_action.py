from unittest.mock import Mock

from PySide6.QtWidgets import QMessageBox

from app.services.cleanup_service import CleanupResult, CleanupService
from app.ui.main_window import MainWindow


def test_manual_cleanup_passes_current_and_preserves_state(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)
    window.continue_button.click()
    window.form_page.title_field.setText("Em edição")
    report, autosave, directory = window.report, window.autosave_service, window.project_directory
    result = CleanupResult(moved_to_trash=[directory], deleted=[directory],
                           skipped=[directory, directory], errors={directory: "error"})
    run = Mock(return_value=result)
    message = Mock()
    monkeypatch.setattr(CleanupService, "run", run)
    monkeypatch.setattr(QMessageBox, "information", message)
    assert window.cleanup_action.text() == "Executar limpeza"
    window.cleanup_action.trigger()
    run.assert_called_once_with(window.app_paths, current_project=directory)
    text = message.call_args.args[2]
    assert "Movidos para a lixeira: 1" in text
    assert "Excluídos definitivamente: 1" in text
    assert "Ignorados: 2" in text
    assert "Erros: 1" in text
    assert window.report is report
    assert window.project_directory == directory
    assert window.autosave_service is autosave
    assert autosave.is_dirty
    assert window.autosave_timer.isActive()
    assert window.debounce_timer.isActive()


def test_manual_cleanup_structural_error_is_friendly(qtbot, monkeypatch):
    run = Mock(side_effect=PermissionError("private details"))
    monkeypatch.setattr(CleanupService, "run", run)
    window = MainWindow()
    qtbot.addWidget(window)
    run.assert_not_called()
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    window.cleanup_action.trigger()
    warning.assert_called_once()
    assert "private details" not in warning.call_args.args[2]
    assert "Traceback" not in warning.call_args.args[2]
