from datetime import date
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QMessageBox

from app.models.party import Party
from app.models.property import Property
from app.models.report import Report
from app.services.document_generator import DocumentGenerator
from app.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot, tmp_path):
    window = MainWindow()
    qtbot.addWidget(window)
    window._set_project(Report(
        title="Casa", inspection_date=date(2026, 10, 2), inspector_name="Ana",
        property=Property(property_type="Casa", address="Rua A"),
        landlord=Party("Bruno"), tenant=Party("Carla"),
    ), tmp_path / "project")
    return window


def test_expected_placeholders_without_masks(window):
    expected = {
        window.form_page.inspection_date_field: "Ex.: 02/10/2026",
        window.form_page.issue_date_field: "Ex.: 02/10/2026",
        window.form_page.postal_code_field: "Ex.: 25000-000",
        window.parties_page.landlord_document_field:
            "Ex.: 123.456.789-00 ou 12.345.678/0001-90",
        window.parties_page.tenant_document_field:
            "Ex.: 123.456.789-00 ou 12.345.678/0001-90",
        window.parties_page.landlord_phone_field: "Ex.: (21) 99999-9999",
        window.parties_page.tenant_phone_field: "Ex.: (21) 99999-9999",
    }
    for field, placeholder in expected.items():
        assert field.placeholderText() == placeholder
        assert field.inputMask() == ""
        field.setText("Texto livre colado")
        assert field.text() == "Texto livre colado"
        field.clear()
        assert field.text() == ""


@pytest.mark.parametrize("name", ["inspection_date", "issue_date"])
def test_generation_blocks_invalid_date_even_when_report_has_old_valid_date(
    window, monkeypatch, name,
):
    window._show_review()
    old = getattr(window.report, name)
    field = getattr(window.form_page, f"{name}_field")
    field.setText("31/02/2026")
    field.editingFinished.emit()
    generate = Mock()
    monkeypatch.setattr(DocumentGenerator, "generate", generate)
    monkeypatch.setattr(QMessageBox, "warning", Mock())
    window.review_page.generate_button.click()
    generate.assert_not_called()
    assert window.pages.currentWidget() is window.form_page
    assert getattr(window.report, name) == old
    assert field.text() == "31/02/2026"
    assert not window.autosave_service.is_dirty


def test_valid_date_navigation_uses_existing_debounce_and_autosave(window):
    window.form_page.inspection_date_field.setText("03/10/2026")
    window.form_page.continue_button.click()
    assert window.pages.currentWidget() is window.parties_page
    assert window.report.inspection_date == date(2026, 10, 3)
    assert window.autosave_service.is_dirty
    assert window.debounce_timer.interval() == 2000
    window.debounce_timer.stop()
    window.debounce_timer.timeout.emit()
    assert not window.autosave_service.is_dirty
    assert window.autosave_timer.interval() == 60000
