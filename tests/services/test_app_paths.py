from pathlib import Path

from app.services.app_paths import AppPaths


def test_override_and_idempotent_structure(tmp_path):
    paths = AppPaths(tmp_path / "VistoriaApp")
    assert paths.app_root == tmp_path / "VistoriaApp"
    assert paths.projects_root == paths.app_root / "Projetos"
    assert paths.trash_root == paths.app_root / "Lixeira"
    assert paths.landlords_file == paths.app_root / "locadores.json"
    paths.ensure_directories()
    paths.ensure_directories()
    assert paths.app_root.is_dir()
    assert paths.projects_root.is_dir()
    assert paths.trash_root.is_dir()
    assert set(paths.app_root.iterdir()) == {paths.projects_root, paths.trash_root}


def test_default_uses_platform_documents_directory(tmp_path, monkeypatch):
    from PySide6.QtCore import QStandardPaths

    calls = []
    def documents(location):
        calls.append(location)
        return str(tmp_path / "Documentos")

    monkeypatch.setattr(QStandardPaths, "writableLocation", documents)
    assert AppPaths().app_root == Path(tmp_path / "Documentos" / "VistoriaApp")
    assert calls == [QStandardPaths.StandardLocation.DocumentsLocation]
