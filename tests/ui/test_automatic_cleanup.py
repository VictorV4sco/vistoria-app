import os
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication

from app.models.report import Report
from app.services.app_paths import AppPaths
from app.services.cleanup_service import CleanupResult, CleanupService
from app.services.project_service import ProjectService
from app.ui.main_window import MainWindow


@pytest.mark.parametrize("has_directory", [False, True])
def test_cleanup_never_runs_on_startup(qtbot, tmp_path, monkeypatch, has_directory):
    run = Mock(return_value=CleanupResult())
    monkeypatch.setattr(CleanupService, "run", run)
    paths = AppPaths(tmp_path / "app")
    directory = paths.projects_root / "current" if has_directory else None
    window = MainWindow(directory, app_paths=paths)
    qtbot.addWidget(window)
    window.show()
    QCoreApplication.processEvents()
    QCoreApplication.processEvents()
    run.assert_not_called()
    assert window.statusBar().currentMessage() == ""


@pytest.mark.parametrize("operation", [
    "create", "open", "navigate", "save", "autosave", "debounce", "backup",
])
def test_project_flow_never_invokes_cleanup(qtbot, tmp_path, monkeypatch, operation):
    run = Mock(return_value=CleanupResult())
    monkeypatch.setattr(CleanupService, "run", run)
    paths = AppPaths(tmp_path / "app")
    existing = paths.projects_root / "existing"
    ProjectService.save(Report(title="Existente"), existing)
    window = MainWindow(app_paths=paths)
    qtbot.addWidget(window)
    if operation == "create":
        window.continue_button.click()
    else:
        window.start_page.open_button.click()
        assert window.project_directory == existing
        if operation == "navigate":
            window.form_page.continue_button.click()
            window.parties_page.continue_button.click()
            window.environments_page.continue_button.click()
            window.review_page.back_button.click()
            window.environments_page.back_button.click()
            window.parties_page.back_button.click()
            window.back_button.click()
        elif operation in ("save", "autosave", "debounce", "backup"):
            window.form_page.title_field.setText("Editado")
            if operation == "save":
                window.save_action.trigger()
            elif operation == "autosave":
                window.autosave_timer.timeout.emit()
            elif operation == "debounce":
                window.debounce_timer.stop()
                window.debounce_timer.timeout.emit()
            else:
                window.save_action.trigger()
                window.recover_backup_action.trigger()
    QCoreApplication.processEvents()
    run.assert_not_called()
    assert existing.is_dir()


def test_old_projects_and_existing_trash_remain_intact_in_normal_flow(qtbot, tmp_path):
    paths = AppPaths(tmp_path / "app")
    old = paths.projects_root / "old"
    trashed = paths.trash_root / "archived"
    for directory in (old, trashed):
        ProjectService.save(Report(title=directory.name), directory)
        (directory / "imagens").mkdir(exist_ok=True)
        (directory / "imagens" / "photo.jpg").write_bytes(b"preserve image")
        (directory / "relatorios").mkdir()
        (directory / "relatorios" / "relatorio-vistoria.docx").write_bytes(b"preserve Word")
        os.utime(directory / "projeto.json", (946684800, 946684800))
    (trashed / ".cleanup.json").write_text(
        '{"trashed_at": "2000-01-01T00:00:00+00:00"}', encoding="utf-8"
    )
    snapshots = {
        directory: {file.relative_to(directory): file.read_bytes()
                    for file in directory.rglob("*") if file.is_file()}
        for directory in (old, trashed)
    }

    def assert_preserved():
        for directory, expected in snapshots.items():
            assert directory.is_dir()
            assert {file.relative_to(directory): file.read_bytes()
                    for file in directory.rglob("*") if file.is_file()} == expected
        assert not (paths.trash_root / "old").exists()
        assert not (paths.projects_root / "archived").exists()

    window = MainWindow(app_paths=paths)
    qtbot.addWidget(window)
    QCoreApplication.processEvents()
    assert_preserved()
    window.continue_button.click()
    window.form_page.continue_button.click()
    window.parties_page.continue_button.click()
    window.environments_page.continue_button.click()
    window.form_page.title_field.setText("Novo projeto")
    window.save_action.trigger()
    window.form_page.title_field.setText("Autosave")
    window.autosave_timer.timeout.emit()
    window.form_page.title_field.setText("Debounce")
    window.debounce_timer.stop()
    window.debounce_timer.timeout.emit()
    window.start_page.open_button.click()
    QCoreApplication.processEvents()
    assert_preserved()
