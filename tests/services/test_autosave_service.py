from pathlib import Path
from unittest.mock import Mock

import pytest

from app.models.report import Report
from app.services.autosave_service import AutosaveService
from app.services.project_service import ProjectService


@pytest.fixture
def save_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    save = Mock(spec=ProjectService.save)
    monkeypatch.setattr(ProjectService, "save", save)
    return save


def test_new_service_starts_clean() -> None:
    assert AutosaveService().is_dirty is False


def test_mark_dirty_is_idempotent_and_state_is_per_instance() -> None:
    service = AutosaveService()
    other = AutosaveService()

    service.mark_dirty()
    service.mark_dirty()

    assert service.is_dirty is True
    assert other.is_dirty is False


def test_clean_service_does_not_save(save_mock: Mock) -> None:
    service = AutosaveService()

    service.save_if_needed(Report(), Path("project"))

    save_mock.assert_not_called()
    assert service.is_dirty is False


def test_dirty_service_delegates_save_and_clears_state_after_success(save_mock: Mock) -> None:
    service = AutosaveService()
    report = Report()
    directory = Path("project")
    service.mark_dirty()

    def check_dirty_during_save(report: Report, project_directory: Path) -> None:
        assert service.is_dirty is True

    save_mock.side_effect = check_dirty_during_save
    service.save_if_needed(report, directory)

    save_mock.assert_called_once_with(report, directory)
    assert save_mock.call_args.args[0] is report
    assert service.is_dirty is False

    service.save_if_needed(report, directory)
    save_mock.assert_called_once_with(report, directory)

    service.mark_dirty()
    service.save_if_needed(report, directory)
    assert save_mock.call_count == 2
    assert service.is_dirty is False


@pytest.mark.parametrize("error", [OSError("disk failed"), ValueError("invalid report")])
def test_failed_save_propagates_error_and_remains_dirty_for_retry(
    save_mock: Mock, error: Exception
) -> None:
    service = AutosaveService()
    report = Report()
    directory = Path("project")
    service.mark_dirty()
    save_mock.side_effect = error

    with pytest.raises(type(error)) as raised:
        service.save_if_needed(report, directory)

    assert raised.value is error
    save_mock.assert_called_once_with(report, directory)
    assert service.is_dirty is True

    save_mock.side_effect = None
    service.save_if_needed(report, directory)

    assert save_mock.call_count == 2
    save_mock.assert_called_with(report, directory)
    assert service.is_dirty is False
