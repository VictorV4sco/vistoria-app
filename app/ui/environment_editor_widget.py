"""Reusable editor bound to one existing Section."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.models.section import Section
from app.ui.section_photos_widget import SectionPhotosWidget


class EnvironmentEditorWidget(QGroupBox):
    changed = Signal()

    remove_requested = Signal()
    move_requested = Signal(int)

    def __init__(self, section: Section, project_directory: Path | None = None) -> None:
        super().__init__("Ambiente")
        self.section = section
        self.project_directory = project_directory
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.name_field = QLineEdit(section.name)
        self.name_field.textChanged.connect(lambda value: self._update("name", value))
        form.addRow("Nome", self.name_field)
        for name, label in (("description", "Descrição"), ("notes", "Observações")):
            field = QTextEdit()
            field.setAcceptRichText(False)
            field.setMaximumHeight(90)
            field.setPlainText(getattr(section, name))
            field.textChanged.connect(
                lambda name=name, field=field: self._update(name, field.toPlainText())
            )
            setattr(self, f"{name}_field", field)
            form.addRow(label, field)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        self.up_button = QPushButton("Mover para cima")
        self.down_button = QPushButton("Mover para baixo")
        self.remove_button = QPushButton("Remover")
        self.up_button.clicked.connect(lambda: self.move_requested.emit(-1))
        self.down_button.clicked.connect(lambda: self.move_requested.emit(1))
        self.remove_button.clicked.connect(self.remove_requested.emit)
        for button in (self.up_button, self.down_button, self.remove_button):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.photos_widget = SectionPhotosWidget(section, project_directory)
        self.photos_widget.changed.connect(self.changed.emit)
        self.add_photo_button = self.photos_widget.add_button
        self.photos_empty_label = self.photos_widget.empty_label
        layout.addWidget(self.photos_widget)

    @property
    def photo_editors(self):
        return self.photos_widget.editors

    def refresh_photos(self) -> None:
        self.photos_widget.refresh()

    def _update(self, name: str, value: str) -> None:
        if getattr(self.section, name) != value:
            setattr(self.section, name, value)
            self.changed.emit()
