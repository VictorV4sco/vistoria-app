import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("relative", [
    "templates/modelo_relatorio.docx", Path("assets/logo_alger.png"),
])
def test_development_resources_are_relative_to_project_not_cwd(monkeypatch, tmp_path, relative):
    from app.utils.resources import resource_path

    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    root = Path(__file__).resolve().parents[2]
    result = resource_path(relative)
    assert result == root / relative
    assert result.is_file()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("relative", [
    Path("templates/modelo_relatorio.docx"), "assets/logo_alger.png",
])
def test_packaged_resources_use_meipass_without_creating_directories(
    monkeypatch, tmp_path, relative,
):
    from app.utils.resources import resource_path

    bundle = tmp_path / "bundle" / "_internal"
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.chdir(tmp_path)
    assert resource_path(relative) == bundle / relative
    assert list(tmp_path.iterdir()) == []
