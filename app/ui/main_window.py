"""Coordinate pages and local project persistence."""

import shutil
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import QInputDialog, QMainWindow, QMessageBox, QStackedWidget

from app.models.report import Report
from app.services.app_paths import AppPaths
from app.services.autosave_service import AutosaveService
from app.services.project_catalog import ProjectCatalogService
from app.services.project_service import ProjectService
from app.ui.environments_page import EnvironmentsPage
from app.ui.inspection_form_page import InspectionFormPage
from app.ui.parties_page import PartiesPage
from app.ui.review_page import ReviewPage
from app.ui.start_page import StartPage


class MainWindow(QMainWindow):
    def __init__(
        self, project_directory: Path | None = None, *, app_paths: AppPaths | None = None,
    ) -> None:
        super().__init__()
        self.app_paths = app_paths if app_paths is not None else AppPaths()
        self.project_directory = project_directory
        self.setWindowTitle("VistoriaApp")
        self.resize(640, 700)
        self.report: Report | None = None
        self.autosave_service = AutosaveService()
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
        self.start_page.open_requested.connect(self._open_project)
        for page in (self.form_page, self.parties_page,
                     self.environments_page, self.review_page):
            page.changed.connect(self._mark_dirty)
        self.review_page.before_generate = self._save_checkpoint
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(60_000)
        self.autosave_timer.timeout.connect(self._autosave_tick)
        self.autosave_timer.start()
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setInterval(2000)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._autosave_tick)
        file_menu = self.menuBar().addMenu("Arquivo")
        new_action = file_menu.addAction("Nova vistoria")
        new_action.triggered.connect(self._show_start)
        open_action = file_menu.addAction("Abrir vistoria existente")
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_project)
        self.save_action = QAction("Salvar", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.setEnabled(False)
        self.save_action.triggered.connect(self._save_project)
        file_menu.addAction(self.save_action)
        self.recover_backup_action = QAction("Recuperar backup", self)
        self.recover_backup_action.setEnabled(False)
        self.recover_backup_action.triggered.connect(self._recover_backup)
        file_menu.addAction(self.recover_backup_action)

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

    @contextmanager
    def _pause_debounce(self) -> Iterator[None]:
        pending = self.debounce_timer.isActive()
        self.debounce_timer.stop()
        try:
            yield
        finally:
            if pending and self.autosave_service.is_dirty:
                self.debounce_timer.start()

    def _start_inspection(self) -> None:
        with self._pause_debounce():
            self._create_inspection()

    def _create_inspection(self) -> None:
        if not self._confirm_pending_changes():
            return
        report_type = "Inicial" if self.initial_radio.isChecked() else "Final"
        report = Report(report_type=report_type)
        directory = self.app_paths.projects_root / f"vistoria-{uuid4().hex}"
        directory_created = False
        try:
            self.app_paths.ensure_directories()
            # Reserve a unique folder; never overwrite an existing project.
            directory.mkdir(exist_ok=False)
            directory_created = True
            ProjectService.save(report, directory)
        except Exception:
            if directory_created:
                # Cleanup must not replace the initial creation error.
                with suppress(OSError):
                    shutil.rmtree(directory)
            QMessageBox.warning(
                self, "Não foi possível criar a vistoria",
                "Não foi possível criar a vistoria. Verifique se a pasta de projetos "
                "está disponível e se você tem permissão para gravar nela.",
            )
            return
        self._set_project(report, directory)

    def _open_project(self) -> None:
        with self._pause_debounce():
            self._load_project()

    def _load_project(self) -> None:
        if not self._confirm_pending_changes():
            return
        try:
            self.app_paths.ensure_directories()
            projects = ProjectCatalogService.list_projects(self.app_paths.projects_root)
            if not projects:
                QMessageBox.information(
                    self, "Nenhuma vistoria disponível",
                    "Não há vistorias válidas na pasta de projetos. Crie uma nova vistoria.",
                )
                return
            labels = [project.label for project in projects]
            selected, accepted = QInputDialog.getItem(
                self, "Abrir vistoria existente", "Escolha a vistoria:", labels, 0, False
            )
            if not accepted:
                return
            directory = projects[labels.index(selected)].directory
            report = ProjectService.load(directory)
        except Exception:
            QMessageBox.warning(
                self, "Não foi possível abrir a vistoria",
                "Não foi possível abrir a vistoria. Verifique se escolheu a pasta "
                "correta e se o arquivo do projeto está disponível e válido.",
            )
            return
        self._set_project(report, directory)

    def _set_project(self, report: Report, directory: Path) -> None:
        """Bind the service's Report to every page only after successful I/O."""
        self.debounce_timer.stop()
        self.autosave_service = AutosaveService()
        self.report = report
        self.project_directory = directory
        self.form_page.set_report(report)
        self.parties_page.set_report(report)
        self.environments_page.set_report(report, directory)
        self.review_page.set_report(report, directory)
        self.save_action.setEnabled(True)
        self.recover_backup_action.setEnabled(True)
        self.statusBar().showMessage(f"Projeto: {directory}")
        self._show_form()

    def _recover_backup(self) -> None:
        with self._pause_debounce():
            self._restore_backup()

    def _restore_backup(self) -> None:
        if self.report is None or self.project_directory is None:
            return
        directory = self.project_directory
        timer_active = self.autosave_timer.isActive()
        self.autosave_timer.stop()
        try:
            if not ProjectService.has_valid_backup(directory):
                QMessageBox.information(
                    self, "Backup indisponível",
                    "Não há backup válido disponível para esta vistoria.",
                )
                return
            if not self._confirm_pending_changes():
                return
            # Saving pending changes can rotate the backup; preview the current one.
            backup = ProjectService.load_backup(directory)
            choice = QMessageBox.question(
                self, "Recuperar backup",
                f"Restaurar o backup da vistoria {backup.title or backup.report_type}?\n"
                "O conteúdo salvo no backup substituirá o arquivo principal do projeto. "
                "Alterações atuais ainda não salvas podem ser perdidas.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice != QMessageBox.StandardButton.Yes:
                return
            ProjectService.restore_backup(directory)
        except Exception:
            QMessageBox.warning(
                self, "Não foi possível recuperar o backup",
                "Não foi possível recuperar o backup. Verifique se os arquivos do projeto "
                "estão disponíveis e válidos e se você tem permissão para gravar na pasta.",
            )
            return
        finally:
            if timer_active:
                self.autosave_timer.start()
        self._set_project(backup, directory)
        self.statusBar().showMessage("Backup restaurado com sucesso")

    def _mark_dirty(self) -> None:
        if self.report is not None and self.project_directory is not None:
            self.autosave_service.mark_dirty()
            self.statusBar().showMessage("Alterações não salvas")
            self.debounce_timer.start()

    def _save_project(self) -> bool:
        return self._persist(manual=True)

    def _persist(self, *, manual: bool = False, warn: bool = False) -> bool:
        if self.report is None or self.project_directory is None:
            return False
        if manual:
            self.autosave_service.mark_dirty()
        if not self.autosave_service.is_dirty:
            self.debounce_timer.stop()
            return True
        try:
            self.autosave_service.save_if_needed(self.report, self.project_directory)
        except Exception:
            self.statusBar().showMessage(
                "Alterações não salvas" if manual else "Falha ao salvar automaticamente"
            )
            if manual or warn:
                QMessageBox.warning(
                    self, "Não foi possível salvar a vistoria",
                    "Não foi possível salvar a vistoria. Verifique se a pasta do projeto "
                    "está disponível e se você tem permissão para gravar nela.",
                )
            return False
        self.debounce_timer.stop()
        self.statusBar().showMessage(
            f"Projeto salvo: {self.project_directory}" if manual else "Salvo automaticamente"
        )
        return True

    def _autosave_tick(self) -> None:
        self._persist()

    def _save_checkpoint(self) -> bool:
        return self._persist(warn=True)

    def _confirm_pending_changes(self) -> bool:
        if not self.autosave_service.is_dirty:
            return True
        choice = QMessageBox.question(
            self, "Alterações não salvas", "Deseja salvar as alterações da vistoria?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Save:
            return self._save_project()
        return choice == QMessageBox.StandardButton.Discard

    def closeEvent(self, event: QCloseEvent) -> None:
        with self._pause_debounce():
            can_close = self._confirm_pending_changes()
        if can_close:
            self.debounce_timer.stop()
            self.autosave_timer.stop()
            event.accept()
        else:
            event.ignore()

    def _show_review(self) -> None:
        if not self._save_checkpoint():
            return
        if self.report is not None:
            self.review_page.set_report(self.report, self.project_directory)
        self.pages.setCurrentWidget(self.review_page)

    def _show_environments(self) -> None:
        if self.report is not None:
            self.environments_page.set_report(self.report, self.project_directory)
        self.pages.setCurrentWidget(self.environments_page)

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
