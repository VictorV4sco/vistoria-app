from unittest.mock import Mock

from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from app.models.report import Report
from app.services.app_paths import AppPaths
from app.services.project_service import ProjectService
from app.ui.main_window import MainWindow


def test_new_project_uses_injected_root_without_folder_dialog(qtbot, tmp_path, monkeypatch):
    paths = AppPaths(tmp_path / "custom")
    window = MainWindow(app_paths=paths)
    qtbot.addWidget(window)
    folder = Mock(side_effect=AssertionError("No filesystem picker"))
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", folder)
    window.continue_button.click()
    assert window.project_directory.parent == paths.projects_root
    assert paths.trash_root.is_dir()
    assert ProjectService.load(window.project_directory) == window.report
    assert not window.autosave_service.is_dirty
    assert not window.debounce_timer.isActive()
    first = window.project_directory
    window.continue_button.click()
    assert window.project_directory != first
    folder.assert_not_called()


def test_selection_lists_only_managed_projects(qtbot, tmp_path, monkeypatch):
    paths = AppPaths(tmp_path / "custom")
    paths.ensure_directories()
    ProjectService.save(Report(title="Casa"), paths.projects_root / "one")
    ProjectService.save(Report(title="Fora"), tmp_path / "outside")
    window = MainWindow(app_paths=paths)
    qtbot.addWidget(window)
    picker = Mock(side_effect=lambda *args: (args[3][0], True))
    monkeypatch.setattr(QInputDialog, "getItem", picker)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", Mock(side_effect=AssertionError()))
    window._open_project()
    assert window.report.title == "Casa"
    assert window.project_directory == paths.projects_root / "one"
    assert len(picker.call_args.args[3]) == 1
    assert not window.autosave_service.is_dirty


def test_empty_catalog_informs_without_dialog(qtbot, tmp_path, monkeypatch):
    window = MainWindow(app_paths=AppPaths(tmp_path))
    qtbot.addWidget(window)
    info = Mock()
    picker = Mock()
    monkeypatch.setattr(QMessageBox, "information", info)
    monkeypatch.setattr(QInputDialog, "getItem", picker)
    window._open_project()
    picker.assert_not_called()
    info.assert_called_once()
    assert window.report is None


def test_managed_root_failure_preserves_loaded_project(qtbot, tmp_path, monkeypatch):
    paths = AppPaths(tmp_path / "custom")
    window = MainWindow(app_paths=paths)
    qtbot.addWidget(window)
    window.continue_button.click()
    report, directory = window.report, window.project_directory
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    monkeypatch.setattr(paths, "ensure_directories", Mock(side_effect=PermissionError("denied")))
    window.continue_button.click()
    assert window.report is report
    assert window.project_directory == directory
    assert list(paths.projects_root.iterdir()) == [directory]
    warning.assert_called_once()
