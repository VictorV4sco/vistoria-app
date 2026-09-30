from datetime import UTC, datetime

import pytest

from app.models.party import Party
from app.models.property import Property
from app.models.report import Report
from app.models.section import Section


def test_create_report_with_default_values() -> None:
    report = Report()

    assert report.id is not None
    assert report.version == 1
    assert report.sections == []
    assert report.created_at is not None
    assert report.updated_at is not None
    assert report.report_type == "Inicial"
    assert report.title == ""
    assert report.code == ""
    assert report.inspection_date is None
    assert report.issue_date is None
    assert report.inspector_name == ""
    assert isinstance(report.property, Property)
    assert isinstance(report.landlord, Party)
    assert isinstance(report.tenant, Party)
    assert report.complementary_information.delivered_keys == ""
    assert report.complementary_information.energy_meter == ""
    assert report.complementary_information.consumer_unit == ""
    assert report.complementary_information.general_notes == ""
    assert report.complementary_information.issue_location == ""
    assert report.protected_from_cleanup is False


def test_default_report_timestamps_are_utc() -> None:
    report = Report()

    assert report.created_at.tzinfo is UTC
    assert report.updated_at.tzinfo is UTC


def test_report_normalizes_aware_timestamps_to_utc() -> None:
    timestamp = datetime.fromisoformat("2026-09-24T10:20:30.123456-03:00")
    report = Report(created_at=timestamp, updated_at=timestamp)

    assert report.created_at == timestamp
    assert report.updated_at == timestamp
    assert report.created_at.tzinfo is UTC
    assert report.updated_at.tzinfo is UTC


@pytest.mark.parametrize("field", ["created_at", "updated_at"])
def test_report_rejects_naive_timestamps(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        Report(**{field: datetime(2026, 9, 24, 10, 20)})


def test_reports_do_not_share_mutable_defaults() -> None:
    report = Report()
    other = Report()

    assert report.property is not other.property
    assert report.landlord is not other.landlord
    assert report.tenant is not other.tenant
    assert report.landlord is not report.tenant
    assert report.complementary_information is not other.complementary_information
    assert report.sections is not other.sections


def test_report_sections_start_as_empty_list() -> None:
    report = Report()

    assert report.sections == []


def test_add_section_keeps_sections_sorted_by_order() -> None:
    report = Report()
    first = Section(name="Sala", order=10)
    second = Section(name="Cozinha", order=20)

    report.add_section(second)
    report.add_section(first)

    assert report.sections == [first, second]
    assert [section.order for section in report.sections] == [10, 20]


def test_remove_section_preserves_remaining_sections() -> None:
    first = Section(name="Sala", order=0)
    second = Section(name="Cozinha", order=1)
    third = Section(name="Quarto", order=2)
    report = Report(sections=[first, second, third])

    report.remove_section(second)

    assert report.sections == [first, third]
    assert [section.order for section in report.sections] == [0, 2]


def test_remove_only_section_leaves_empty_list() -> None:
    section = Section(name="Sala")
    report = Report(sections=[section])

    report.remove_section(section)

    assert report.sections == []


def test_reorder_sections_uses_updated_order() -> None:
    first = Section(name="Sala", order=0)
    second = Section(name="Cozinha", order=1)
    third = Section(name="Quarto", order=2)
    report = Report(sections=[first, second, third])
    first.order = 20
    second.order = 30
    third.order = 10

    report.reorder_sections()

    assert report.sections == [third, first, second]
    assert [section.order for section in report.sections] == [10, 20, 30]


def test_reorder_sections_with_empty_list() -> None:
    report = Report()

    report.reorder_sections()

    assert report.sections == []


def test_reports_do_not_share_sections() -> None:
    report = Report()
    other = Report()
    section = Section(name="Sala")

    report.add_section(section)

    assert report.sections == [section]
    assert other.sections == []
    assert report.sections is not other.sections


@pytest.mark.parametrize("report_type", ["Inicial", "Final"])
def test_report_accepts_only_supported_types(report_type: str) -> None:
    report = Report(report_type=report_type)
    assert report.report_type == report_type
    report.report_type = "Final" if report_type == "Inicial" else "Inicial"
    assert report.report_type != report_type


@pytest.mark.parametrize(
    "invalid", ["Periódica", "Outra", "", "inicial", "Final ", "Livre", None, 1],
)
def test_report_rejects_invalid_type_on_creation_and_assignment(invalid: object) -> None:
    with pytest.raises(ValueError, match="report_type.*Inicial.*Final"):
        Report(report_type=invalid)
    report = Report(report_type="Final")
    with pytest.raises(ValueError, match="report_type.*Inicial.*Final"):
        report.report_type = invalid
    assert report.report_type == "Final"


@pytest.mark.parametrize("index, offset, expected", [
    (1, -1, [1, 0, 2]), (1, 1, [0, 2, 1]),
    (0, -1, [0, 1, 2]), (2, 1, [0, 1, 2]),
])
def test_move_section_preserves_identity_and_normalizes_order(index, offset, expected):
    sections = [Section(name=str(i), order=i * 10) for i in range(3)]
    report = Report(sections=sections.copy())
    report.move_section(sections[index], offset)
    assert all(actual is sections[i] for actual, i in zip(report.sections, expected, strict=True))
    if 0 <= index + offset < 3:
        assert [section.order for section in report.sections] == [0, 1, 2]
    else:
        assert [section.order for section in report.sections] == [0, 10, 20]
