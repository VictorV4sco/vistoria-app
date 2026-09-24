import json
from datetime import date, datetime
from pathlib import Path

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
    report.title = "Final"
    report.sections.clear()

    ProjectService.save(report, tmp_path)

    assert json.loads((tmp_path / "projeto.json").read_text(encoding="utf-8")) == report_to_dict(
        report
    )
    assert ProjectService.load(tmp_path) == report
    assert list(tmp_path.iterdir()) == [tmp_path / "projeto.json"]


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
