from copy import deepcopy
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QMessageBox

from app.models.party import Party
from app.models.report import Report
from app.services.app_paths import AppPaths
from app.services.landlord_service import LandlordService
from app.ui.main_window import MainWindow
from app.ui.parties_page import PartiesPage


@pytest.fixture
def agenda(tmp_path):
    paths = AppPaths(tmp_path / "app")
    service = LandlordService(paths)
    service.save(Party("Ana", "123", "111", "ana@example.com", "Rua A"))
    service.save(Party("Bruno", "456"))
    return service


@pytest.fixture
def page(qtbot, agenda):
    page = PartiesPage(app_paths=agenda.app_paths)
    qtbot.addWidget(page)
    page.set_report(Report())
    return page


def test_selector_starts_empty_and_lists_saved_landlords(page):
    combo = page.landlord_selector
    assert combo.currentIndex() == 0
    assert combo.itemText(0) == "Selecione um locador..."
    assert "Ana" in combo.itemText(1)
    assert "Bruno" in combo.itemText(2)
    assert not page.delete_landlord_button.isEnabled()


def test_select_copies_all_fields_and_emits_only_for_real_change(page, agenda):
    changed = Mock()
    page.changed.connect(changed)
    original = page.report.landlord
    page.landlord_selector.setCurrentIndex(1)
    expected = agenda.list_landlords()[0]
    assert page.report.landlord is original
    assert page.report.landlord == expected
    assert page.report.landlord is not page._landlords[0]
    for name in vars(expected):
        assert getattr(page, f"landlord_{name}_field").text() == getattr(expected, name)
    changed.assert_called_once()
    page.landlord_selector.setCurrentIndex(0)
    page.landlord_selector.setCurrentIndex(1)
    changed.assert_called_once()
    agenda.save(Party("Ana atualizada", "123", address="Rua B"))
    assert page.report.landlord == expected
    page._landlords[0].name = "Outra edição"
    assert page.report.landlord == expected


def test_save_uses_current_fields_without_dirtying_report(page, agenda):
    page.landlord_name_field.setText("João")
    page.landlord_document_field.setText("789")
    page.landlord_phone_field.setText("222")
    changed = Mock()
    page.changed.connect(changed)
    before = deepcopy(page.report)
    page.save_landlord_button.click()
    assert agenda.list_landlords()[-1] == page.report.landlord
    assert page.report == before
    changed.assert_not_called()
    page.save_landlord_button.click()
    assert len(agenda.list_landlords()) == 3


def test_empty_fields_do_not_save(page, agenda, monkeypatch):
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    before = agenda.app_paths.landlords_file.read_bytes()
    page.save_landlord_button.click()
    assert agenda.app_paths.landlords_file.read_bytes() == before
    assert warning.call_args.args[2] == (
        "Informe pelo menos o nome ou CPF/CNPJ do locador para salvá-lo na agenda."
    )


@pytest.mark.parametrize("field, value", [("phone", "111"), ("email", "ana@example.com")])
@pytest.mark.parametrize("existing", [False, True])
def test_save_without_identity_warns_without_writing_or_changing_inspection(
    qtbot, tmp_path, monkeypatch, field, value, existing,
):
    paths = AppPaths(tmp_path / "app")
    service = LandlordService(paths)
    if existing:
        service.save(Party("Ana", "123"))
    page = PartiesPage(app_paths=paths)
    qtbot.addWidget(page)
    report = Report()
    page.set_report(report)
    getattr(page, f"landlord_{field}_field").setText(value)
    assert getattr(report.landlord, field) == value
    before_report = deepcopy(report)
    before_file = paths.landlords_file.read_bytes() if existing else None
    changed, warning = Mock(), Mock()
    page.changed.connect(changed)
    monkeypatch.setattr(QMessageBox, "warning", warning)
    page.save_landlord_button.click()
    warning.assert_called_once()
    assert warning.call_args.args[2] == (
        "Informe pelo menos o nome ou CPF/CNPJ do locador para salvá-lo na agenda."
    )
    assert report == before_report
    changed.assert_not_called()
    page.continue_button.click()
    assert report == before_report
    if existing:
        assert paths.landlords_file.read_bytes() == before_file
    else:
        assert not paths.landlords_file.exists()


@pytest.mark.parametrize("field, value", [("name", "Ana"), ("document", "12345678900")])
def test_ui_can_save_with_name_or_document_alone(page, agenda, field, value):
    getattr(page, f"landlord_{field}_field").setText(value)
    page.save_landlord_button.click()
    assert page.report.landlord in agenda.list_landlords()


@pytest.mark.parametrize("confirm", [False, True])
def test_delete_only_changes_agenda_after_confirmation(page, agenda, monkeypatch, confirm):
    page.landlord_selector.setCurrentIndex(1)
    before = deepcopy(page.report)
    changed = Mock()
    page.changed.connect(changed)
    question = Mock(return_value=(QMessageBox.StandardButton.Yes if confirm
                                 else QMessageBox.StandardButton.No))
    monkeypatch.setattr(QMessageBox, "question", question)
    page.delete_landlord_button.click()
    question.assert_called_once()
    assert len(agenda.list_landlords()) == (1 if confirm else 2)
    assert page.report == before
    assert page.landlord_name_field.text() == "Ana"
    changed.assert_not_called()


def test_set_report_resets_selection_without_writing_or_changing_reports(page, monkeypatch):
    page.landlord_selector.setCurrentIndex(1)
    previous = deepcopy(page.report)
    current = Report(landlord=Party("Carla", "999"))
    before = deepcopy(current)
    save, delete, changed = Mock(), Mock(), Mock()
    monkeypatch.setattr(page.landlord_service, "save", save)
    monkeypatch.setattr(page.landlord_service, "delete", delete)
    page.changed.connect(changed)
    old_report = page.report
    page.set_report(current)
    page.set_report(current)
    assert page.landlord_selector.currentIndex() == 0
    assert page.landlord_name_field.text() == "Carla"
    assert current == before
    assert old_report == previous
    for action in (save, delete, changed):
        action.assert_not_called()


def test_corruption_is_silent_on_load_and_friendly_on_use(qtbot, agenda, monkeypatch):
    agenda.app_paths.landlords_file.write_text("broken", encoding="utf-8")
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    page = PartiesPage(app_paths=agenda.app_paths)
    qtbot.addWidget(page)
    page.set_report(Report(landlord=Party("Ana")))
    warning.assert_not_called()
    page.landlord_selector.about_to_show.emit()
    page.save_landlord_button.click()
    assert warning.call_count == 2
    for call in warning.call_args_list:
        assert "agenda de locadores" in call.args[2]
        assert "Traceback" not in call.args[2]
    assert agenda.app_paths.landlords_file.read_text() == "broken"


@pytest.mark.parametrize("operation", ["select", "save", "delete"])
def test_agenda_io_errors_do_not_escape_or_change_report(page, monkeypatch, operation):
    page.landlord_selector.setCurrentIndex(1)
    before = deepcopy(page.report)
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    method = {"select": "list_landlords", "save": "save", "delete": "delete"}[operation]
    monkeypatch.setattr(page.landlord_service, method,
                        Mock(side_effect=PermissionError("private path /secret")))
    if operation == "select":
        page.landlord_selector.about_to_show.emit()
    else:
        getattr(page, f"{operation}_landlord_button").click()
    warning.assert_called_once()
    assert "private" not in warning.call_args.args[2]
    assert "/secret" not in warning.call_args.args[2]
    assert page.report == before


def test_main_window_injects_storage_and_agenda_selection_uses_autosave(qtbot, tmp_path):
    paths = AppPaths(tmp_path / "custom")
    LandlordService(paths).save(Party("Ana", "123"))
    window = MainWindow(app_paths=paths)
    qtbot.addWidget(window)
    window.continue_button.click()
    assert window.parties_page.landlord_service.app_paths is paths
    window.parties_page.landlord_selector.setCurrentIndex(1)
    assert window.autosave_service.is_dirty
    assert window.debounce_timer.isActive()
