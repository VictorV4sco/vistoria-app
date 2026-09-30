"""Coordinate pages and the inspection held in memory."""

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMainWindow, QStackedWidget

from app.models.report import Report
from app.ui.environments_page import EnvironmentsPage
from app.ui.inspection_form_page import InspectionFormPage
from app.ui.parties_page import PartiesPage
from app.ui.review_page import ReviewPage
from app.ui.start_page import StartPage


class MainWindow(QMainWindow):
    def __init__(self, project_directory: Path | None = None) -> None:
        super().__init__()
        self.project_directory = project_directory
        self.setWindowTitle("VistoriaApp")
        self.resize(640, 700)
        self.report: Report | None = None
        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)
        self.start_page = StartPage()
        self.form_page = InspectionFormPage()
        self.parties_page = PartiesPage()
        self.environments_page = EnvironmentsPage()
        self.review_page = ReviewPage()
        for page in (
            self.start_page, self.form_page, self.parties_page, self.environments_page,
            self.review_page,
        ):
            self.pages.addWidget(page)
        self.start_page.continue_requested.connect(self._start_inspection)
        self.form_page.back_requested.connect(self._show_start)
        self.form_page.continue_requested.connect(self._show_parties)
        self.parties_page.back_requested.connect(self._show_form)
        self.parties_page.continue_requested.connect(self._show_environments)
        self.environments_page.back_requested.connect(self._show_parties)
        self.environments_page.continue_requested.connect(self._show_review)
        self.review_page.back_requested.connect(self._show_environments)
        self.environments_page.directory_requested.connect(self._choose_project_directory)

    @property
    def initial_radio(self):
        return self.start_page.initial_radio

    @property
    def final_radio(self):
        return self.start_page.final_radio

    @property
    def continue_button(self):
        return self.start_page.continue_button

    @property
    def back_button(self):
        return self.form_page.back_button

    def _start_inspection(self) -> None:
        report_type = "Inicial" if self.initial_radio.isChecked() else "Final"
        self.report = Report(report_type=report_type)
        self.form_page.set_report(self.report)
        self.parties_page.set_report(self.report)
        self.environments_page.set_report(self.report, self.project_directory)
        self.review_page.set_report(self.report, self.project_directory)
        self._show_form()

    def _show_review(self) -> None:
        if self.report is not None:
            self.review_page.set_report(self.report, self.project_directory)
        self.pages.setCurrentWidget(self.review_page)

    def _show_environments(self) -> None:
        if self.report is not None:
            self.environments_page.set_report(self.report, self.project_directory)
        self.pages.setCurrentWidget(self.environments_page)

    def _choose_project_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Selecionar pasta do projeto")
        if directory:
            self.project_directory = Path(directory)
            self._show_environments()

    def _show_parties(self) -> None:
        if self.report is not None:
            self.parties_page.set_report(self.report)
        self.pages.setCurrentWidget(self.parties_page)
        self.parties_page.landlord_name_field.setFocus()

    def _show_form(self) -> None:
        self.pages.setCurrentWidget(self.form_page)
        self.form_page.title_field.setFocus()

    def _show_start(self) -> None:
        self.pages.setCurrentWidget(self.start_page)
        self.continue_button.setFocus()
