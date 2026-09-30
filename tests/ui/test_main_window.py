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
def test_continue_creates_report_and_opens_placeholder(
    window: MainWindow, qtbot: QtBot, report_type: str,
) -> None:
    if report_type == "Final":
        qtbot.mouseClick(window.final_radio, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.continue_button, Qt.MouseButton.LeftButton)
    assert isinstance(window.report, Report)
    assert window.report.report_type == report_type
    assert window.pages.currentWidget() is window.placeholder_page
    assert window.placeholder_title.text() == f"Nova Vistoria {report_type}"
    assert window.placeholder_title.isVisible()


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
