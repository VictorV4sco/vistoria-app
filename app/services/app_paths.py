"""Resolve visible, platform-specific application storage with injectable roots."""

from pathlib import Path

from PySide6.QtCore import QStandardPaths


class AppPaths:
    def __init__(self, app_root: Path | None = None) -> None:
        self.app_root = Path(app_root) if app_root is not None else self.default_root()
        self.projects_root = self.app_root / "Projetos"
        self.trash_root = self.app_root / "Lixeira"
        self.landlords_file = self.app_root / "locadores.json"

    @staticmethod
    def default_root() -> Path:
        documents = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation
        )
        return (Path(documents) if documents else Path.home() / "Documents") / "VistoriaApp"

    def ensure_directories(self) -> None:
        self.projects_root.mkdir(parents=True, exist_ok=True)
        self.trash_root.mkdir(parents=True, exist_ok=True)
