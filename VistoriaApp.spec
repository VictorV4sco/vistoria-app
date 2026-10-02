# Build this specification on Windows to produce VistoriaApp.exe.
from pathlib import Path

root = Path(SPECPATH).resolve()

a = Analysis(
    [str(root / "app" / "main.py")],
    pathex=[str(root)],
    datas=[
        (str(root / "templates" / "modelo_relatorio.docx"), "templates"),
        (str(root / "assets" / "logo_alger.png"), "assets"),
    ],
    hiddenimports=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VistoriaApp",
    console=False,
    strip=False,
    upx=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="VistoriaApp",
    strip=False,
    upx=False,
)
