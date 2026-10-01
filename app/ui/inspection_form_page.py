"""Edit inspection and property data directly on the current Report."""

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.report import Report


class InspectionFormPage(QWidget):
    changed = Signal()

    back_requested = Signal()
    continue_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.report: Report | None = None
        self._loading = False
        self._text_fields: dict[str, QLineEdit] = {}
        self._date_fields: dict[str, QDateEdit] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        inspection_box = QGroupBox("DADOS DA VISTORIA")
        inspection_layout = QFormLayout(inspection_box)
        inspection_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.report_type_field = QLineEdit()
        self.report_type_field.setReadOnly(True)
        inspection_layout.addRow("Tipo da vistoria", self.report_type_field)
        for name, label in (
            ("title", "Título"), ("code", "Código / referência"),
        ):
            self._add_text(inspection_layout, name, label)
        for name, label in (
            ("inspection_date", "Data da vistoria"), ("issue_date", "Data de emissão"),
        ):
            field = QDateEdit()
            field.setCalendarPopup(True)
            field.setDisplayFormat("dd/MM/yyyy")
            field.setDateRange(QDate(1, 1, 1), QDate(9999, 12, 31))
            field.setSpecialValueText("Não informada")
            field.setDate(field.minimumDate())
            field.setToolTip("Use a data mínima para deixar como Não informada.")
            field.dateChanged.connect(
                lambda value, name=name, field=field: self._update(
                    name, None if value == field.minimumDate() else value.toPython()
                )
            )
            self._date_fields[name] = field
            setattr(self, f"{name}_field", field)
            inspection_layout.addRow(label, field)
        self._add_text(inspection_layout, "inspector_name", "Responsável pela vistoria")
        content_layout.addWidget(inspection_box)

        property_box = QGroupBox("DADOS DO IMÓVEL")
        property_layout = QFormLayout(property_box)
        property_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.property_type_field = QComboBox()
        self.property_type_field.addItems([
            "", "Casa", "Sobrado", "Apartamento", "Loja", "Sala comercial", "Terreno", "Outro",
        ])
        self.property_type_field.currentTextChanged.connect(
            lambda value: self._update("property_type", value, property_field=True)
        )
        property_layout.addRow("Tipo do imóvel", self.property_type_field)
        self.description_field = QTextEdit()
        self.description_field.setAcceptRichText(False)
        self.description_field.setMaximumHeight(90)
        self.description_field.textChanged.connect(
            lambda: self._update(
                "description", self.description_field.toPlainText(), property_field=True
            )
        )
        property_layout.addRow("Descrição resumida", self.description_field)
        for name, label in (
            ("address", "Endereço"), ("number", "Número"), ("complement", "Complemento"),
            ("neighborhood", "Bairro"), ("city", "Cidade"), ("state", "Estado"),
            ("postal_code", "CEP"),
        ):
            self._add_text(property_layout, name, label, property_field=True)
        content_layout.addWidget(property_box)
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

    def _add_text(
        self, layout: QFormLayout, name: str, label: str, property_field: bool = False,
    ) -> None:
        field = QLineEdit()
        field.textChanged.connect(
            lambda value: self._update(name, value, property_field=property_field)
        )
        self._text_fields[name] = field
        setattr(self, f"{name}_field", field)
        layout.addRow(label, field)

    def _update(self, name: str, value: object, property_field: bool = False) -> None:
        if self.report is not None and not self._loading:
            target = self.report.property if property_field else self.report
            if getattr(target, name) != value:
                setattr(target, name, value)
                self.changed.emit()

    def set_report(self, report: Report) -> None:
        """Load widgets without changing either the old or the new report."""
        self._loading = True
        try:
            self.report = report
            self.report_type_field.setText(report.report_type)
            for name, field in self._text_fields.items():
                target = report if name in ("title", "code", "inspector_name") else report.property
                field.setText(getattr(target, name))
            for name, field in self._date_fields.items():
                value = getattr(report, name)
                field.setDate(QDate(value) if value is not None else field.minimumDate())
            property_type = report.property.property_type
            if self.property_type_field.findText(property_type) < 0:
                self.property_type_field.addItem(property_type)
            self.property_type_field.setCurrentText(property_type)
            self.description_field.setPlainText(report.property.description)
        finally:
            self._loading = False
