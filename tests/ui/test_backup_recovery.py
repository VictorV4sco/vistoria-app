from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QMessageBox

from app.models.report import Report
from app.services.project_service import ProjectService
from app.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot, tmp_path):
    directory = tmp_path / "project"
    ProjectService.save(Report(title="Backup", report_type="Final"), directory)
    ProjectService.save(Report(title="Principal"), directory)
    window = MainWindow()
    qtbot.addWidget(window)
    window._set_project(ProjectService.load(directory), directory)
    return window


@pytest.fixture
def dialogs(monkeypatch):
    question = Mock(return_value=QMessageBox.StandardButton.Yes)
    warning = Mock()
    information = Mock()
    monkeypatch.setattr(QMessageBox, "question", question)
    monkeypatch.setattr(QMessageBox, "warning", warning)
    monkeypatch.setattr(QMessageBox, "information", information)
    return question, warning, information


def test_action_enabled_only_with_loaded_project(qtbot, window):
    empty = MainWindow()
    qtbot.addWidget(empty)
    assert not empty.recover_backup_action.isEnabled()
    assert window.recover_backup_action.isEnabled()
    assert window.recover_backup_action.text() == "Recuperar backup"
    assert window.recover_backup_action in window.menuBar().actions()[0].menu().actions()


@pytest.mark.parametrize("corrupt", [False, True])
@pytest.mark.parametrize("dirty", [False, True])
def test_unavailable_backup_preserves_state(window, dialogs, corrupt, dirty):
    directory = window.project_directory
    backup = directory / "projeto.backup.json"
    if corrupt:
        backup.write_text("invalid", encoding="utf-8")
    else:
        backup.unlink()
    if dirty:
        window.form_page.title_field.setText("Em edição")
    report, autosave = window.report, window.autosave_service
    window.recover_backup_action.trigger()
    assert window.report is report
    assert window.project_directory == directory
    assert window.autosave_service is autosave
    assert autosave.is_dirty == dirty
    dialogs[0].assert_not_called()
    dialogs[2].assert_called_once()
    assert ProjectService.load(directory).title == "Principal"


@pytest.mark.parametrize("dirty", [False, True])
def test_cancel_confirmation_preserves_state(window, dialogs, dirty):
    if dirty:
        window.form_page.title_field.setText("Em edição")
        dialogs[0].side_effect = [QMessageBox.StandardButton.Discard, QMessageBox.StandardButton.No]
    else:
        dialogs[0].return_value = QMessageBox.StandardButton.No
    report, directory, autosave = window.report, window.project_directory, window.autosave_service
    before = (directory / "projeto.json").read_bytes()
    window.recover_backup_action.trigger()
    assert dialogs[0].call_count == (2 if dirty else 1)
    text = dialogs[0].call_args.args[2]
    assert "Backup" in text
    assert "arquivo principal" in text
    assert "não salvas" in text
    assert window.report is report
    assert window.autosave_service is autosave
    assert (directory / "projeto.json").read_bytes() == before
    assert autosave.is_dirty == dirty
    dialogs[0].side_effect = None
    dialogs[0].return_value = QMessageBox.StandardButton.Discard


def test_success_restores_and_rebinds_clean(window, dialogs, monkeypatch):
    directory = window.project_directory
    backup = ProjectService.load_backup(directory)
    old_autosave = window.autosave_service
    timer = window.autosave_timer
    original_load = ProjectService.load
    load = Mock(side_effect=OSError("post-restore load must not run"))
    monkeypatch.setattr(ProjectService, "load", load)
    monkeypatch.setattr(ProjectService, "load_backup", Mock(return_value=backup))
    restore = Mock(wraps=ProjectService.restore_backup)
    monkeypatch.setattr(ProjectService, "restore_backup", restore)
    window.recover_backup_action.trigger()
    restore.assert_called_once_with(directory)
    load.assert_not_called()
    assert window.report is backup
    assert original_load(directory) == backup
    assert window.project_directory == directory
    assert window.autosave_service is not old_autosave
    assert not window.autosave_service.is_dirty
    for page in (window.form_page, window.parties_page,
                 window.environments_page, window.review_page):
        assert page.report is window.report
    assert window.statusBar().currentMessage() == "Backup restaurado com sucesso"
    assert timer is window.autosave_timer
    assert timer.isActive()


@pytest.mark.parametrize("choice,fails", [("Cancel", False), ("Discard", False),
                                         ("Save", False), ("Save", True)])
def test_dirty_protection_reused(window, dialogs, monkeypatch, choice, fails):
    report, directory = window.report, window.project_directory
    window.form_page.title_field.setText("Em edição")
    dialogs[0].side_effect = [getattr(QMessageBox.StandardButton, choice),
                              QMessageBox.StandardButton.Yes]
    calls = []
    original_save = ProjectService.save
    original_restore = ProjectService.restore_backup

    def save(*args):
        calls.append("save")
        if fails:
            raise OSError("private error")
        original_save(*args)

    def restore(*args):
        calls.append("restore")
        original_restore(*args)

    monkeypatch.setattr(ProjectService, "save", save)
    monkeypatch.setattr(ProjectService, "restore_backup", restore)
    window.recover_backup_action.trigger()
    if choice == "Cancel" or fails:
        assert calls == (["save"] if fails else [])
        assert dialogs[0].call_count == 1
        assert window.report is report
        assert window.autosave_service.is_dirty
    else:
        assert calls == (["save", "restore"] if choice == "Save" else ["restore"])
        assert not window.autosave_service.is_dirty
        # Save rotates the backup: confirmation and restoration use its current version.
        expected = "Principal" if choice == "Save" else "Backup"
        assert window.report.title == expected
        assert expected in dialogs[0].call_args.args[2]
    assert window.project_directory == directory
    dialogs[0].side_effect = None
    dialogs[0].return_value = QMessageBox.StandardButton.Discard


@pytest.mark.parametrize("method", ["has_valid_backup", "load_backup", "restore_backup"])
@pytest.mark.parametrize("dirty", [False, True])
def test_failures_preserve_memory(window, dialogs, monkeypatch, method, dirty):
    if dirty:
        window.form_page.title_field.setText("Em edição")
        dialogs[0].side_effect = [QMessageBox.StandardButton.Discard,
                                  QMessageBox.StandardButton.Yes]
    report, directory, autosave = window.report, window.project_directory, window.autosave_service
    monkeypatch.setattr(
        ProjectService, method, Mock(side_effect=PermissionError("private details"))
    )
    window.recover_backup_action.trigger()
    assert window.report is report
    assert window.project_directory == directory
    assert window.autosave_service is autosave
    assert autosave.is_dirty == dirty
    for page in (window.form_page, window.parties_page,
                 window.environments_page, window.review_page):
        assert page.report is report
    dialogs[1].assert_called_once()
    text = dialogs[1].call_args.args[2]
    assert "Não foi possível" in text
    assert "Traceback" not in text
    assert "private details" not in text
    assert window.autosave_timer.isActive()
    dialogs[0].side_effect = None
    dialogs[0].return_value = QMessageBox.StandardButton.Discard


def test_autosave_paused_during_confirmation(window, dialogs):
    def confirm(*args):
        assert not window.autosave_timer.isActive()
        return QMessageBox.StandardButton.No

    dialogs[0].side_effect = confirm
    window.recover_backup_action.trigger()
    assert window.autosave_timer.isActive()
