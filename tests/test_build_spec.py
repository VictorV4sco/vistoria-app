from pathlib import Path
from runpy import run_path
from types import SimpleNamespace
from unittest.mock import Mock


def test_spec_uses_only_application_assets_and_windowed_onedir(monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[1]
    analysis = Mock(return_value=SimpleNamespace(pure=[], scripts=[], binaries=[], datas=[]))
    exe = Mock()
    collect = Mock()
    monkeypatch.chdir(tmp_path)
    run_path(str(root / "VistoriaApp.spec"), init_globals={
        "SPECPATH": str(root), "Analysis": analysis, "PYZ": Mock(),
        "EXE": exe, "COLLECT": collect,
    })
    assert analysis.call_args.args[0] == [str(root / "app" / "main.py")]
    assert analysis.call_args.kwargs["pathex"] == [str(root)]
    assert analysis.call_args.kwargs["datas"] == [
        (str(root / "templates" / "modelo_relatorio.docx"), "templates"),
        (str(root / "assets" / "logo_alger.png"), "assets"),
    ]
    for source, _ in analysis.call_args.kwargs["datas"]:
        assert Path(source).is_file()
    assert analysis.call_args.kwargs["hiddenimports"] == []
    assert exe.call_args.kwargs["name"] == "VistoriaApp"
    assert exe.call_args.kwargs["console"] is False
    assert exe.call_args.kwargs["exclude_binaries"] is True
    assert exe.call_args.kwargs["upx"] is False
    collect.assert_called_once()
    assert collect.call_args.args[0] is exe.return_value
    assert collect.call_args.kwargs["name"] == "VistoriaApp"
    assert collect.call_args.kwargs["upx"] is False
