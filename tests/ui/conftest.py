import pytest
from PySide6.QtWidgets import QFileDialog


@pytest.fixture(autouse=True)
def project_folder_dialog(monkeypatch, tmp_path):
    """Never open a native folder dialog in UI tests."""
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(tmp_path))
