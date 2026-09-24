import json
from copy import deepcopy
from datetime import UTC, date, datetime
from pathlib import PurePosixPath, PureWindowsPath

import pytest

from app.models.complementary_information import ComplementaryInformation
from app.models.party import Party
from app.models.photo import Photo
from app.models.property import Property
from app.models.report import Report
from app.models.section import Section
from app.services.report_serialization import report_from_dict, report_to_dict


@pytest.fixture
def project_data() -> dict:
    return {
        "version": 7,
        "id": "report-id",
        "report_type": "Inicial",
        "title": "Vistoria da casa",
        "code": "REF-42",
        "inspection_date": "2026-09-24",
        "issue_date": "2026-09-25",
        "inspector_name": "Ana",
        "created_at": "2026-09-23T13:20:30.123456+00:00",
        "updated_at": "2026-09-25T17:35:45.654321+00:00",
        "protected_from_cleanup": True,
        "property": {
            "property_type": "Casa",
            "description": "Sobrado",
            "address": "Rua A",
            "number": "42",
            "complement": "Fundos",
            "neighborhood": "Centro",
            "city": "Niterói",
            "state": "RJ",
            "postal_code": "24000-000",
        },
        "landlord": {
            "name": "Maria",
            "document": "123",
            "phone": "21999999999",
            "email": "maria@example.com",
            "address": "Rua B",
        },
        "tenant": {
            "name": "José",
            "document": "456",
            "phone": "21888888888",
            "email": "jose@example.com",
            "address": "Rua C",
        },
        "complementary_information": {
            "delivered_keys": "3",
            "energy_meter": "M-1",
            "consumer_unit": "UC-2",
            "general_notes": "Sem ressalvas",
            "issue_location": "Niterói",
        },
        "sections": [
            {
                "id": "section-b",
                "name": "Sala",
                "description": "Ampla",
                "notes": "Pintura nova",
                "order": 20,
                "photos": [
                    {
                        "id": "photo-b",
                        "file_path": "imagens/foto-b.jpg",
                        "caption": "Janela",
                        "order": 30,
                    },
                    {
                        "id": "photo-a",
                        "file_path": "imagens/foto-a.png",
                        "caption": "Vista geral",
                        "order": 10,
                    },
                ],
            },
            {
                "id": "section-a",
                "name": "Cozinha",
                "description": "Azulejada",
                "notes": "",
                "order": 10,
                "photos": [],
            },
        ],
    }


@pytest.fixture
def report(project_data: dict) -> Report:
    return Report(
        id="report-id",
        version=7,
        report_type="Inicial",
        title="Vistoria da casa",
        code="REF-42",
        inspector_name="Ana",
        protected_from_cleanup=True,
        inspection_date=date(2026, 9, 24),
        issue_date=date(2026, 9, 25),
        created_at=datetime.fromisoformat("2026-09-23T10:20:30.123456-03:00"),
        updated_at=datetime.fromisoformat("2026-09-25T14:35:45.654321-03:00"),
        property=Property(**project_data["property"]),
        landlord=Party(**project_data["landlord"]),
        tenant=Party(**project_data["tenant"]),
        complementary_information=ComplementaryInformation(
            **project_data["complementary_information"]
        ),
        sections=[
            Section(
                id="section-b",
                name="Sala",
                description="Ampla",
                notes="Pintura nova",
                order=20,
                photos=[
                    Photo(id="photo-b", file_path="imagens/foto-b.jpg", caption="Janela", order=30),
                    Photo(
                        id="photo-a",
                        file_path="imagens/foto-a.png",
                        caption="Vista geral",
                        order=10,
                    ),
                ],
            ),
            Section(id="section-a", name="Cozinha", description="Azulejada", order=10),
        ],
    )


def test_report_to_dict_matches_project_format(report: Report, project_data: dict) -> None:
    data = report_to_dict(report)

    assert data == project_data
    assert json.loads(json.dumps(data)) == project_data


def test_report_from_dict_restores_domain_types_and_values(
    report: Report, project_data: dict
) -> None:
    restored = report_from_dict(project_data)

    assert isinstance(restored, Report)
    assert restored == report
    assert type(restored.inspection_date) is date
    assert type(restored.issue_date) is date
    assert isinstance(restored.created_at, datetime)
    assert isinstance(restored.updated_at, datetime)
    assert isinstance(restored.property, Property)
    assert isinstance(restored.landlord, Party)
    assert isinstance(restored.tenant, Party)
    assert isinstance(restored.complementary_information, ComplementaryInformation)
    assert all(isinstance(section, Section) for section in restored.sections)
    assert all(isinstance(photo, Photo) for photo in restored.sections[0].photos)


def test_round_trip_preserves_ids_order_and_relative_paths(report: Report) -> None:
    restored = report_from_dict(report_to_dict(report))

    assert restored == report
    assert [section.id for section in restored.sections] == ["section-b", "section-a"]
    assert [section.order for section in restored.sections] == [20, 10]
    assert [photo.id for photo in restored.sections[0].photos] == ["photo-b", "photo-a"]
    assert [photo.order for photo in restored.sections[0].photos] == [30, 10]
    for photo in restored.sections[0].photos:
        assert not PurePosixPath(photo.file_path).is_absolute()
        assert not PureWindowsPath(photo.file_path).is_absolute()


def test_default_report_round_trip_preserves_empty_dates_and_utc_timestamps() -> None:
    report = Report()

    data = report_to_dict(report)
    restored = report_from_dict(data)

    assert data["inspection_date"] is None
    assert data["issue_date"] is None
    assert data["created_at"] == report.created_at.isoformat()
    assert data["updated_at"] == report.updated_at.isoformat()
    assert restored == report
    assert restored.sections == []
    assert restored.created_at.tzinfo is UTC
    assert restored.updated_at.tzinfo is UTC


def test_reconstructed_reports_do_not_share_mutable_data(project_data: dict) -> None:
    original_data = deepcopy(project_data)
    first = report_from_dict(project_data)
    second = report_from_dict(project_data)

    first.sections[0].photos[0].caption = "Alterada"
    first.sections[0].photos.append(Photo(file_path="imagens/nova.jpg"))
    first.sections[1].photos.append(Photo(file_path="imagens/cozinha.jpg"))
    first.sections.append(Section(name="Quarto"))
    first.property.city = "Outra cidade"
    first.landlord.name = "Outro locador"
    first.tenant.name = "Outro locatário"
    first.complementary_information.general_notes = "Alteradas"

    assert report_to_dict(second) == original_data
    assert project_data == original_data


def test_serialized_data_does_not_share_mutable_data(report: Report) -> None:
    original = deepcopy(report)
    data = report_to_dict(report)

    data["sections"][0]["photos"][0]["caption"] = "Alterada"
    data["sections"][0]["photos"].clear()
    data["sections"].clear()
    data["property"]["city"] = "Outra cidade"

    assert report == original


@pytest.mark.parametrize("offset", ["+00:00", "-03:00", "+05:30"])
def test_timestamps_round_trip_as_json_compatible_utc(project_data: dict, offset: str) -> None:
    timestamp = f"2026-09-24T10:20:30.123456{offset}"
    project_data["created_at"] = timestamp
    project_data["updated_at"] = timestamp
    report = report_from_dict(project_data)

    data = json.loads(json.dumps(report_to_dict(report)))
    restored = report_from_dict(data)

    expected = datetime.fromisoformat(timestamp).astimezone(UTC)
    assert data["created_at"] == expected.isoformat()
    assert data["updated_at"] == expected.isoformat()
    for value in (report.created_at, report.updated_at, restored.created_at, restored.updated_at):
        assert value == expected
        assert value.tzinfo is UTC
    assert data["inspection_date"] == "2026-09-24"
    assert data["issue_date"] == "2026-09-25"
    assert type(restored.inspection_date) is date
    assert type(restored.issue_date) is date
    assert restored.inspection_date == date(2026, 9, 24)
    assert restored.issue_date == date(2026, 9, 25)


@pytest.mark.parametrize("field", ["created_at", "updated_at"])
def test_deserialization_rejects_timestamps_without_timezone(
    project_data: dict, field: str
) -> None:
    project_data[field] = "2026-09-24T10:20:30"

    with pytest.raises(ValueError, match=field):
        report_from_dict(project_data)


@pytest.mark.parametrize("field", ["created_at", "updated_at"])
def test_serialization_rejects_timestamps_changed_to_naive(field: str) -> None:
    report = Report()
    setattr(report, field, datetime(2026, 9, 24, 10, 20))

    with pytest.raises(ValueError, match=field):
        report_to_dict(report)


def test_serialization_normalizes_edited_timestamps_to_utc() -> None:
    report = Report()
    timestamp = datetime.fromisoformat("2026-09-24T10:20:30-03:00")
    report.created_at = timestamp
    report.updated_at = timestamp

    data = report_to_dict(report)

    assert data["created_at"] == "2026-09-24T13:20:30+00:00"
    assert data["updated_at"] == "2026-09-24T13:20:30+00:00"
    assert report.created_at is timestamp
    assert report.updated_at is timestamp


@pytest.mark.parametrize("version", [1, 7])
def test_version_is_preserved_at_top_level(version: int) -> None:
    report = Report(version=version)

    data = report_to_dict(report)

    assert data["version"] == version
    assert report_from_dict(data).version == version
