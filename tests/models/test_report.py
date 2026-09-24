from app.models.report import Report


def test_create_report_with_default_values() -> None:
    report = Report()

    assert report.id is not None
    assert report.version == 1
    assert report.sections == []
    assert report.created_at is not None
    assert report.updated_at is not None
