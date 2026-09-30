"""Reusable editor bound to one existing Section."""

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


class EnvironmentEditorWidget(QGroupBox):
    remove_requested = Signal()
    move_requested = Signal(int)

    def __init__(self, section: Section) -> None:
        super().__init__("Ambiente")
        self.section = section
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.name_field = QLineEdit(section.name)
        self.name_field.textChanged.connect(lambda value: setattr(section, "name", value))
        form.addRow("Nome", self.name_field)
        for name, label in (("description", "Descrição"), ("notes", "Observações")):
            field = QTextEdit()
            field.setAcceptRichText(False)
            field.setMaximumHeight(90)
            field.setPlainText(getattr(section, name))
            field.textChanged.connect(
                lambda name=name, field=field: setattr(section, name, field.toPlainText())
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
