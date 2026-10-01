"""Edit the existing parties directly on the current Report."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models.report import Report


class PartiesPage(QWidget):
    changed = Signal()

    back_requested = Signal()
    continue_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.report: Report | None = None
        self._loading = False
        self._text_fields: dict[tuple[str, str], QLineEdit] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        self.title = QLabel("Partes envolvidas")
        layout.addWidget(self.title)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        for role, title in (("landlord", "LOCADOR"), ("tenant", "LOCATÁRIO")):
            box = QGroupBox(title)
            form = QFormLayout(box)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            for name, label in (
                ("name", "Nome"), ("document", "CPF / CNPJ"), ("phone", "Telefone"),
                ("email", "E-mail"), ("address", "Endereço"),
            ):
                field = QLineEdit()
                field.textChanged.connect(
                    lambda value, role=role, name=name: self._update(role, name, value)
                )
                self._text_fields[role, name] = field
                setattr(self, f"{role}_{name}_field", field)
                form.addRow(label, field)
            content_layout.addWidget(box)
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        buttons = QHBoxLayout()
        self.back_button = QPushButton("Voltar")
        self.continue_button = QPushButton("Continuar")
        self.back_button.clicked.connect(self.back_requested.emit)
        self.continue_button.clicked.connect(self.continue_requested.emit)
        buttons.addWidget(self.back_button)
        buttons.addStretch()
        buttons.addWidget(self.continue_button)
        layout.addLayout(buttons)

    def _update(self, role: str, name: str, value: str) -> None:
        if self.report is not None and not self._loading:
            target = getattr(self.report, role)
            if getattr(target, name) != value:
                setattr(target, name, value)
                self.changed.emit()

    def set_report(self, report: Report) -> None:
        """Load values without mutating either report or replacing its parties."""
        self._loading = True
        try:
            self.report = report
            for (role, name), field in self._text_fields.items():
                field.setText(getattr(getattr(report, role), name))
        finally:
            self._loading = False
