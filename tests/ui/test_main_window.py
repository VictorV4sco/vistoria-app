import pytest
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from app.models.report import Report
from app.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot: QtBot) -> MainWindow:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    return window


def test_initial_is_selected_by_default(window: MainWindow) -> None:
    assert window.windowTitle() == "VistoriaApp"
    assert window.initial_radio.isChecked()
    assert not window.final_radio.isChecked()
    assert window.pages.currentWidget() is window.start_page
    assert window.report is None


def test_inspection_types_are_exclusive(window: MainWindow, qtbot: QtBot) -> None:
    qtbot.mouseClick(window.final_radio, Qt.MouseButton.LeftButton)
    assert window.final_radio.isChecked()
    assert not window.initial_radio.isChecked()
    qtbot.mouseClick(window.final_radio, Qt.MouseButton.LeftButton)
    assert window.final_radio.isChecked()
    qtbot.mouseClick(window.initial_radio, Qt.MouseButton.LeftButton)
    assert window.initial_radio.isChecked()
    assert not window.final_radio.isChecked()


@pytest.mark.parametrize("report_type", ["Inicial", "Final"])
def test_continue_creates_report_and_opens_form(
    window: MainWindow, qtbot: QtBot, report_type: str,
) -> None:
    if report_type == "Final":
        qtbot.mouseClick(window.final_radio, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.continue_button, Qt.MouseButton.LeftButton)
    assert isinstance(window.report, Report)
    assert window.report.report_type == report_type
    assert window.pages.currentWidget() is window.form_page
    assert window.form_page.report_type_field.text() == report_type
    assert window.form_page.report_type_field.isVisible()


def test_back_returns_to_start_and_continue_creates_new_report(
    window: MainWindow, qtbot: QtBot,
) -> None:
    qtbot.mouseClick(window.continue_button, Qt.MouseButton.LeftButton)
    previous_report = window.report
    qtbot.mouseClick(window.back_button, Qt.MouseButton.LeftButton)
    assert window.pages.currentWidget() is window.start_page
    assert window.continue_button.isVisible()
    qtbot.mouseClick(window.final_radio, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.continue_button, Qt.MouseButton.LeftButton)
    assert window.report is not previous_report
    assert window.report.id != previous_report.id
    assert window.report.report_type == "Final"


@pytest.mark.parametrize("report_type", ["Inicial", "Final"])
def test_navigation_preserves_report(window, qtbot, report_type):
    window.final_radio.setChecked(report_type == "Final")
    qtbot.mouseClick(window.continue_button, Qt.MouseButton.LeftButton)
    report = window.report
    window.form_page.title_field.setText("Preenchido")
    qtbot.mouseClick(window.form_page.continue_button, Qt.MouseButton.LeftButton)
    assert window.pages.currentWidget() is window.parties_page
    assert window.parties_page.title.text() == "Partes envolvidas"
    assert window.report is report
    qtbot.mouseClick(window.parties_page.back_button, Qt.MouseButton.LeftButton)
    assert window.pages.currentWidget() is window.form_page
    assert window.form_page.title_field.text() == "Preenchido"
    qtbot.mouseClick(window.back_button, Qt.MouseButton.LeftButton)
    assert window.report is report
    assert report.title == "Preenchido"
    assert window.isVisible()
    window.initial_radio.setChecked(report_type == "Final")
    window.final_radio.setChecked(report_type == "Inicial")
    assert report.report_type == report_type
    qtbot.mouseClick(window.continue_button, Qt.MouseButton.LeftButton)
    assert window.report is not report
    assert window.report.report_type != report_type
    assert window.form_page.title_field.text() == ""


def test_restart_same_type_creates_new_report(window, qtbot):
    qtbot.mouseClick(window.continue_button, Qt.MouseButton.LeftButton)
    report = window.report
    qtbot.mouseClick(window.back_button, Qt.MouseButton.LeftButton)
    assert window.report is report
    qtbot.mouseClick(window.continue_button, Qt.MouseButton.LeftButton)
    assert window.report is not report
    assert window.report.report_type == report.report_type


def test_parties_navigation_preserves_report_and_original_parties(window, qtbot):
    qtbot.mouseClick(window.continue_button, Qt.MouseButton.LeftButton)
    report = window.report
    parties = (report.landlord, report.tenant)
    report.landlord.document = "Documento existente"
    qtbot.mouseClick(window.form_page.continue_button, Qt.MouseButton.LeftButton)
    assert window.parties_page.report is report
    assert window.parties_page.landlord_document_field.text() == "Documento existente"
    window.parties_page.landlord_name_field.setText("Ana")
    window.parties_page.tenant_name_field.setText("Bruno")
    qtbot.mouseClick(window.parties_page.back_button, Qt.MouseButton.LeftButton)
    assert window.pages.currentWidget() is window.form_page
    assert window.report is report
    qtbot.mouseClick(window.form_page.continue_button, Qt.MouseButton.LeftButton)
    assert window.parties_page.landlord_name_field.text() == "Ana"
    assert window.parties_page.tenant_name_field.text() == "Bruno"
    qtbot.mouseClick(window.parties_page.continue_button, Qt.MouseButton.LeftButton)
    assert window.pages.currentWidget() is window.environments_page
    assert window.environments_page.title.text() == "Ambientes da vistoria"
    assert window.environments_page.title.isVisible()
    assert window.report is report
    qtbot.mouseClick(window.environments_page.back_button, Qt.MouseButton.LeftButton)
    assert window.pages.currentWidget() is window.parties_page
    assert window.parties_page.landlord_name_field.text() == "Ana"
    assert window.parties_page.tenant_name_field.text() == "Bruno"
    assert report.landlord is parties[0]
    assert report.tenant is parties[1]


def test_new_inspection_rebinds_parties_without_changing_previous_report(window, qtbot):
    qtbot.mouseClick(window.continue_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.form_page.continue_button, Qt.MouseButton.LeftButton)
    previous = window.report
    window.parties_page.landlord_name_field.setText("Ana")
    qtbot.mouseClick(window.parties_page.back_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.form_page.back_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.continue_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.form_page.continue_button, Qt.MouseButton.LeftButton)
    assert window.parties_page.report is window.report
    assert window.report is not previous
    assert window.parties_page.landlord_name_field.text() == ""
    window.parties_page.landlord_name_field.setText("Carla")
    assert window.report.landlord.name == "Carla"
    assert previous.landlord.name == "Ana"
