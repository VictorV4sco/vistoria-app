import pytest
from PySide6.QtWidgets import QFileDialog, QInputDialog


@pytest.fixture(autouse=True)
def project_folder_dialog(monkeypatch, tmp_path):
    from app.services.app_paths import AppPaths

    monkeypatch.setattr(AppPaths, "default_root", staticmethod(lambda: tmp_path / "VistoriaApp"))
    monkeypatch.setattr(QInputDialog, "getItem", lambda *args: (args[3][0], True))
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(tmp_path))


@pytest.fixture(autouse=True)
def discard_on_close(monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Discard)
