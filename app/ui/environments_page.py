"""Manage the current Report's sections in memory."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models.report import Report
from app.models.section import Section
from app.ui.environment_editor_widget import EnvironmentEditorWidget


class EnvironmentsPage(QWidget):
    back_requested = Signal()
    continue_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.report: Report | None = None
        self.editors: list[EnvironmentEditorWidget] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        self.title = QLabel("Ambientes da vistoria")
        layout.addWidget(self.title)
        self.add_button = QPushButton("Adicionar ambiente")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self._add)
        layout.addWidget(self.add_button)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.empty_label = QLabel(
            "Nenhum ambiente adicionado. Clique em Adicionar ambiente para começar."
        )
        self.empty_label.setWordWrap(True)
        self.content_layout.addWidget(self.empty_label)
        self.content_layout.addStretch()
        self.scroll.setWidget(content)
        layout.addWidget(self.scroll)
        buttons = QHBoxLayout()
        self.back_button = QPushButton("Voltar")
        self.continue_button = QPushButton("Continuar")
        self.back_button.clicked.connect(self.back_requested.emit)
        self.continue_button.clicked.connect(self.continue_requested.emit)
        buttons.addWidget(self.back_button)
        buttons.addStretch()
        buttons.addWidget(self.continue_button)
        layout.addLayout(buttons)

    def set_report(self, report: Report) -> None:
        self.report = report
        self.add_button.setEnabled(True)
        self._refresh()

    def _refresh(self) -> None:
        for editor in self.editors:
            self.content_layout.removeWidget(editor)
            editor.hide()
            editor.deleteLater()
        self.editors = []
        if self.report is None:
            return
        for index, section in enumerate(self.report.sections):
            editor = EnvironmentEditorWidget(section)
            editor.remove_requested.connect(lambda section=section: self._remove(section))
            editor.move_requested.connect(
                lambda offset, section=section: self._move(section, offset)
            )
            editor.up_button.setEnabled(index > 0)
            editor.down_button.setEnabled(index < len(self.report.sections) - 1)
            self.editors.append(editor)
            self.content_layout.insertWidget(index + 1, editor)
        self.empty_label.setVisible(not self.editors)

    def _add(self) -> None:
        if self.report is None:
            return
        order = max((section.order for section in self.report.sections), default=-1) + 1
        section = Section(name="Novo ambiente", order=order)
        self.report.add_section(section)
        self._refresh()
        editor = self.editors[-1]
        editor.name_field.setFocus()
        self.scroll.ensureWidgetVisible(editor)

    def _remove(self, section: Section) -> None:
        if self.report is not None:
            self.report.remove_section(section)
            self._refresh()

    def _move(self, section: Section, offset: int) -> None:
        if self.report is not None:
            self.report.move_section(section, offset)
            self._refresh()
