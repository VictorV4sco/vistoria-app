from copy import deepcopy
from datetime import date
from pathlib import Path
from zipfile import ZipFile

import pytest
from docx import Document
from docxtpl import DocxTemplate

from app.models.report import Report
from app.services.document_generator import DocumentGenerator


@pytest.fixture
def report() -> Report:
    return Report(
        title="Vistoria — São Gonçalo & <Anexo>",
        report_type="Periódica",
        inspection_date=date(2026, 9, 4),
        inspector_name="João da Conceição",
    )


def test_generate_valid_docx_with_general_fields(
    tmp_path: Path, report: Report, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "relatório.docx"
    before = deepcopy(report)
    monkeypatch.chdir(tmp_path)

    DocumentGenerator.generate(report, tmp_path / "project", destination)

    with ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert "word/document.xml" in archive.namelist()
    document = Document(destination)
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    for value in (report.title, report.report_type, report.inspector_name, "04/09/2026"):
        assert value in text
    assert "{{" not in text
    assert report == before
    assert list(tmp_path.iterdir()) == [destination]


def test_missing_inspection_date_does_not_render_none(tmp_path: Path, report: Report) -> None:
    report.inspection_date = None
    before = deepcopy(report)
    destination = tmp_path / "report.docx"

    DocumentGenerator.generate(report, tmp_path, destination)

    text = "\n".join(paragraph.text for paragraph in Document(destination).paragraphs)
    assert report.title in text
    assert "None" not in text
    assert "Data da vistoria:" not in text
    assert report == before


def test_success_replaces_existing_document(tmp_path: Path, report: Report) -> None:
    destination = tmp_path / "report.docx"
    Document().save(destination)

    DocumentGenerator.generate(report, tmp_path, destination)

    assert report.title in "\n".join(p.text for p in Document(destination).paragraphs)
    assert list(tmp_path.iterdir()) == [destination]


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("stage", ["render", "save", "replace"])
def test_generation_failure_preserves_destination_and_cleans_temporary_files(
    tmp_path: Path, report: Report, monkeypatch: pytest.MonkeyPatch,
    existing: bool, stage: str,
) -> None:
    destination = tmp_path / "report.docx"
    if existing:
        Document().save(destination)
    before_files = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    before_report = deepcopy(report)

    def fail_render(self: DocxTemplate, *args: object, **kwargs: object) -> None:
        raise ValueError("render failed")

    def fail_save(self: DocxTemplate, path: Path, **kwargs: object) -> None:
        path = Path(path)
        assert path != destination
        assert path.is_relative_to(tmp_path)
        path.write_bytes(b"partial docx")
        raise OSError("save failed")

    def fail_replace(source: Path, target: Path) -> None:
        assert target == destination
        assert report.title in "\n".join(p.text for p in Document(source).paragraphs)
        raise PermissionError("replace failed")

    if stage == "render":
        monkeypatch.setattr(DocxTemplate, "render", fail_render)
    elif stage == "save":
        monkeypatch.setattr(DocxTemplate, "save", fail_save)
    else:
        monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(ValueError if stage == "render" else OSError, match=f"{stage} failed"):
        DocumentGenerator.generate(report, tmp_path, destination)

    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before_files
    assert report == before_report
