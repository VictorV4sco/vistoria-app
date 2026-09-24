from app.models.party import Party
from app.models.property import Property
from app.models.report import Report


def test_create_report_with_default_values() -> None:
    report = Report()

    assert report.id is not None
    assert report.version == 1
    assert report.sections == []
    assert report.created_at is not None
    assert report.updated_at is not None
    assert report.report_type == ""
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


def test_reports_do_not_share_mutable_defaults() -> None:
    report = Report()
    other = Report()

    assert report.property is not other.property
    assert report.landlord is not other.landlord
    assert report.tenant is not other.tenant
    assert report.landlord is not report.tenant
    assert report.complementary_information is not other.complementary_information
    assert report.sections is not other.sections
