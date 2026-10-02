from datetime import date
from unittest.mock import Mock

import pytest

from app.models.property import Property
from app.models.report import Report
from app.ui.inspection_form_page import InspectionFormPage


@pytest.fixture
def report():
    return Report(
        title="Rua das Flores", code="REF-10", inspector_name="Ana",
        inspection_date=date(2026, 9, 24), issue_date=date(2026, 9, 30),
        property=Property(
            property_type="Apartamento", description="Dois quartos\nUma sala",
            address="Rua das Flores", number="10", complement="Apto 2",
            neighborhood="Centro", city="Niterói", state="RJ", postal_code="24000-000",
        ),
    )


@pytest.fixture
def page(qtbot, report):
    page = InspectionFormPage()
    qtbot.addWidget(page)
    page.set_report(report)
    page.show()
    return page


@pytest.mark.parametrize("report_type", ["Inicial", "Final"])
def test_type_is_read_only(page, report, report_type):
    report.report_type = report_type
    page.set_report(report)
    assert page.report_type_field.text() == report_type
    assert page.report_type_field.isReadOnly()


def test_loads_all_values(page, report):
    for name in ("title", "code", "inspector_name"):
        assert getattr(page, f"{name}_field").text() == getattr(report, name)
    for name in ("inspection_date", "issue_date"):
        assert getattr(page, f"{name}_field").text() == getattr(report, name).strftime("%d/%m/%Y")
    assert page.property_type_field.currentText() == report.property.property_type
    assert page.description_field.toPlainText() == report.property.description
    for name in ("address", "number", "complement", "neighborhood", "city", "state", "postal_code"):
        assert getattr(page, f"{name}_field").text() == getattr(report.property, name)


@pytest.mark.parametrize("name", ["title", "code", "inspector_name"])
def test_edit_report_text(page, report, name, qtbot):
    field = getattr(page, f"{name}_field")
    field.clear()
    qtbot.keyClicks(field, "Novo valor")
    assert getattr(report, name) == "Novo valor"


@pytest.mark.parametrize("name", [
    "address", "number", "complement", "neighborhood", "city", "state", "postal_code",
])
def test_edit_property_text(page, report, name):
    original_property = report.property
    getattr(page, f"{name}_field").setText("Novo valor")
    assert report.property is original_property
    assert getattr(report.property, name) == "Novo valor"


def test_edit_property_type_and_description(page, report):
    page.property_type_field.setCurrentText("Casa")
    page.description_field.setPlainText("Nova descrição\nSegundo andar")
    assert report.property.property_type == "Casa"
    assert report.property.description == "Nova descrição\nSegundo andar"


@pytest.mark.parametrize("name", ["inspection_date", "issue_date"])
def test_edit_dates(page, report, name):
    field = getattr(page, f"{name}_field")
    field.setText("15/01/2027")
    field.editingFinished.emit()
    assert getattr(report, name) == date(2027, 1, 15)
    field.clear()
    field.editingFinished.emit()
    assert getattr(report, name) is None


def test_empty_report_and_rebinding(page, report):
    new_report = Report()
    page.set_report(new_report)
    assert new_report.inspection_date is None
    assert new_report.issue_date is None
    assert new_report.property.property_type == ""
    assert page.inspection_date_field.text() == ""
    page.title_field.setText("Nova vistoria")
    assert new_report.title == "Nova vistoria"
    assert report.title == "Rua das Flores"
    assert report.property.property_type == "Apartamento"


def test_property_type_options_include_loja_in_requested_order(page):
    combo = page.property_type_field
    assert [combo.itemText(i) for i in range(combo.count())] == [
        "", "Casa", "Sobrado", "Apartamento", "Loja", "Sala comercial", "Terreno", "Outro",
    ]


def test_property_type_loads_legacy_value(page, report):
    report.property.property_type = "Galpão"
    page.set_report(report)
    assert page.property_type_field.currentText() == "Galpão"
    assert report.property.property_type == "Galpão"


@pytest.mark.parametrize("name", ["inspection_date", "issue_date"])
@pytest.mark.parametrize("text", ["31/02/2026", "2/10/2026", "02/10/26", "texto"])
def test_invalid_date_is_kept_visible_without_changing_report(page, report, name, text):
    field = getattr(page, f"{name}_field")
    before = getattr(report, name)
    changed = Mock()
    page.changed.connect(changed)
    field.setText(text)
    assert getattr(report, name) == before
    field.editingFinished.emit()
    assert getattr(report, name) == before
    assert field.text() == text
    assert "DD/MM/AAAA" in field.toolTip()
    assert getattr(page, f"{name}_error_label").isVisible()
    changed.assert_not_called()
    page.continue_button.click()
    assert not page.validate_dates()


def test_valid_date_commits_once_and_loading_does_not_emit_changed(page, report):
    changed = Mock()
    page.changed.connect(changed)
    page.set_report(report)
    changed.assert_not_called()
    page.inspection_date_field.setText("02/10/2026")
    changed.assert_not_called()
    page.inspection_date_field.editingFinished.emit()
    assert report.inspection_date == date(2026, 10, 2)
    changed.assert_called_once()
    page.inspection_date_field.editingFinished.emit()
    page.continue_button.click()
    changed.assert_called_once()


def test_invalid_date_blocks_navigation_until_corrected(page):
    continued = Mock()
    page.continue_requested.connect(continued)
    page.inspection_date_field.setText("31/02/2026")
    page.continue_button.click()
    continued.assert_not_called()
    page.inspection_date_field.setText("02/10/2026")
    page.continue_button.click()
    continued.assert_called_once()


def test_rebinding_clears_invalid_date_feedback(page, report):
    page.inspection_date_field.setText("31/02/2026")
    page.inspection_date_field.editingFinished.emit()
    page.set_report(Report())
    assert page.inspection_date_field.text() == ""
    assert not page.inspection_date_error_label.isVisible()
    assert page.validate_dates()
    assert report.inspection_date == date(2026, 9, 24)
