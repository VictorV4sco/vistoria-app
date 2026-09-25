import json
from datetime import date, datetime
from pathlib import Path
from typing import TextIO

import pytest

from app.models.complementary_information import ComplementaryInformation
from app.models.party import Party
from app.models.photo import Photo
from app.models.property import Property
from app.models.report import Report
from app.models.section import Section
from app.services.project_service import ProjectService
from app.services.report_serialization import report_to_dict


@pytest.fixture
def report() -> Report:
    return Report(
        id="report-1",
        version=7,
        report_type="Inicial",
        title="Vistoria — São Gonçalo",
        code="REF-42",
        inspection_date=date(2026, 9, 24),
        issue_date=date(2026, 9, 25),
        inspector_name="João",
        created_at=datetime.fromisoformat("2026-09-24T10:20:30.123456+00:00"),
        updated_at=datetime.fromisoformat("2026-09-25T11:21:31.654321+00:00"),
        protected_from_cleanup=True,
        property=Property(
            property_type="Casa", description="Sobrado", address="Rua das Flores",
            number="42", complement="Fundos", neighborhood="Centro", city="São Gonçalo",
            state="RJ", postal_code="24400-000",
        ),
        landlord=Party(
            name="José", document="123", phone="21999999999",
            email="jose@example.com", address="Rua A",
        ),
        tenant=Party(
            name="Ana", document="456", phone="21888888888",
            email="ana@example.com", address="Rua B",
        ),
        complementary_information=ComplementaryInformation(
            delivered_keys="3", energy_meter="M-1", consumer_unit="UC-2",
            general_notes="Sem ressalvas", issue_location="São Gonçalo",
        ),
        sections=[
            Section(
                id="section-b", name="Sala", description="Ampla", notes="Pintura nova",
                order=20,
                photos=[
                    Photo(id="photo-b", file_path="imagens/b.jpg", caption="Janela", order=30),
                    Photo(id="photo-a", file_path="imagens/a.png", caption="Visão geral", order=10),
                ],
            ),
            Section(id="section-a", name="Cozinha", description="Azulejada", order=10),
        ],
    )


def test_save_creates_project_directory_and_json(tmp_path: Path, report: Report) -> None:
    directory = tmp_path / "projetos" / "vistoria"
    assert not directory.exists()

    ProjectService.save(report, directory)

    assert directory.is_dir()
    assert (directory / "projeto.json").is_file()
    assert list(directory.iterdir()) == [directory / "projeto.json"]


def test_save_writes_valid_readable_utf8_json(tmp_path: Path, report: Report) -> None:
    ProjectService.save(report, tmp_path)

    content = (tmp_path / "projeto.json").read_text(encoding="utf-8")
    assert json.loads(content) == report_to_dict(report)
    assert "Vistoria — São Gonçalo" in content
    assert '\n    "' in content


def test_load_reconstructs_complete_report(tmp_path: Path, report: Report) -> None:
    (tmp_path / "projeto.json").write_text(
        json.dumps(report_to_dict(report), ensure_ascii=False), encoding="utf-8"
    )

    loaded = ProjectService.load(tmp_path)

    assert isinstance(loaded, Report)
    assert loaded == report
    assert isinstance(loaded.property, Property)
    assert isinstance(loaded.landlord, Party)
    assert isinstance(loaded.tenant, Party)
    assert isinstance(loaded.complementary_information, ComplementaryInformation)
    assert all(isinstance(section, Section) for section in loaded.sections)
    assert all(isinstance(photo, Photo) for photo in loaded.sections[0].photos)


def test_round_trip_preserves_all_data_ids_dates_and_order(tmp_path: Path, report: Report) -> None:
    ProjectService.save(report, tmp_path)

    loaded = ProjectService.load(tmp_path)

    assert loaded == report
    assert loaded.id == "report-1"
    assert [section.id for section in loaded.sections] == ["section-b", "section-a"]
    assert [photo.id for photo in loaded.sections[0].photos] == ["photo-b", "photo-a"]
    assert loaded.inspection_date == report.inspection_date
    assert loaded.issue_date == report.issue_date
    assert type(loaded.inspection_date) is date
    assert type(loaded.issue_date) is date
    assert loaded.created_at == report.created_at
    assert loaded.updated_at == report.updated_at
    assert isinstance(loaded.created_at, datetime)
    assert isinstance(loaded.updated_at, datetime)


def test_default_report_round_trip(tmp_path: Path) -> None:
    report = Report()

    ProjectService.save(report, tmp_path)

    assert ProjectService.load(tmp_path) == report


def test_save_again_replaces_previous_content(tmp_path: Path, report: Report) -> None:
    ProjectService.save(report, tmp_path)
    previous = (tmp_path / "projeto.json").read_bytes()
    report.title = "Final"
    report.sections.clear()

    ProjectService.save(report, tmp_path)

    assert json.loads((tmp_path / "projeto.json").read_text(encoding="utf-8")) == report_to_dict(
        report
    )
    assert ProjectService.load(tmp_path) == report
    assert (tmp_path / "projeto.backup.json").read_bytes() == previous
    assert {path.name for path in tmp_path.iterdir()} == {"projeto.json", "projeto.backup.json"}


def test_third_save_keeps_only_immediately_previous_version(tmp_path: Path, report: Report) -> None:
    ProjectService.save(report, tmp_path)
    report.title = "Segunda versão"
    ProjectService.save(report, tmp_path)
    previous = (tmp_path / "projeto.json").read_bytes()
    report.title = "Terceira versão"

    ProjectService.save(report, tmp_path)

    assert ProjectService.load(tmp_path) == report
    assert (tmp_path / "projeto.backup.json").read_bytes() == previous
    assert {path.name for path in tmp_path.iterdir()} == {"projeto.json", "projeto.backup.json"}


@pytest.mark.parametrize("existing_project", [False, True])
def test_partial_write_failure_preserves_existing_files(
    tmp_path: Path, report: Report, monkeypatch: pytest.MonkeyPatch, existing_project: bool
) -> None:
    project = tmp_path / "projeto.json"
    backup = tmp_path / "projeto.backup.json"
    previous = json.dumps(report_to_dict(report)).encode("utf-8")
    if existing_project:
        project.write_bytes(previous)
        backup.write_bytes(b'{"title": "older version"}')

    def fail_dump(data: dict, file: TextIO, **kwargs: object) -> None:
        file.write('{"title": ')
        file.flush()
        raise OSError("write failed")

    monkeypatch.setattr(json, "dump", fail_dump)
    with pytest.raises(OSError, match="write failed"):
        ProjectService.save(report, tmp_path)

    if existing_project:
        assert project.read_bytes() == previous
        assert backup.read_bytes() == b'{"title": "older version"}'
    else:
        assert not project.exists()
        assert not backup.exists()


@pytest.mark.parametrize("failed_target", ["projeto.backup.json", "projeto.json"])
def test_replace_failure_preserves_old_backup_and_expected_project_version(
    tmp_path: Path, report: Report, monkeypatch: pytest.MonkeyPatch, failed_target: str
) -> None:
    project = tmp_path / "projeto.json"
    backup = tmp_path / "projeto.backup.json"
    previous = json.dumps(report_to_dict(report)).encode("utf-8")
    older = b'{"title": "older version"}'
    project.write_bytes(previous)
    backup.write_bytes(older)
    report.title = "Nova versão"
    replace = Path.replace

    def fail_replace(source: Path, target: Path) -> Path:
        if target.name == failed_target:
            raise PermissionError("replace failed")
        return replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(PermissionError, match="replace failed"):
        ProjectService.save(report, tmp_path)

    if failed_target == "projeto.json":
        assert project.read_bytes() == previous
        assert json.loads((tmp_path / "projeto.tmp").read_text("utf-8")) == report_to_dict(
            report
        )
    else:
        assert ProjectService.load(tmp_path) == report
        assert not (tmp_path / "projeto.tmp").exists()
    assert backup.read_bytes() == older
    assert (tmp_path / "projeto.backup.tmp").read_bytes() == previous


def test_partial_backup_write_failure_preserves_both_versions(
    tmp_path: Path, report: Report, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "projeto.json"
    backup = tmp_path / "projeto.backup.json"
    previous = json.dumps(report_to_dict(report)).encode("utf-8")
    older = b'{"title": "older version"}'
    project.write_bytes(previous)
    backup.write_bytes(older)

    def fail_write_bytes(path: Path, data: bytes) -> int:
        with path.open("wb") as file:
            file.write(data[:10])
        raise OSError("backup write failed")

    monkeypatch.setattr(Path, "write_bytes", fail_write_bytes)
    with pytest.raises(OSError, match="backup write failed"):
        ProjectService.save(report, tmp_path)

    assert project.read_bytes() == previous
    assert backup.read_bytes() == older


@pytest.mark.parametrize("directory_exists", [False, True])
def test_load_missing_project_raises_file_not_found(tmp_path: Path, directory_exists: bool) -> None:
    directory = tmp_path / "vistoria"
    if directory_exists:
        directory.mkdir()

    with pytest.raises(FileNotFoundError) as error:
        ProjectService.load(directory)

    assert Path(error.value.filename) == directory / "projeto.json"


@pytest.mark.parametrize("content", ["", '{"id": "report-1",', '{"id": "report-1"} trailing'])
def test_load_invalid_json_raises_without_returning_partial_data(
    tmp_path: Path, content: str
) -> None:
    (tmp_path / "projeto.json").write_text(content, encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        ProjectService.load(tmp_path)
