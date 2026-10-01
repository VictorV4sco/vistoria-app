"""Edit complementary information, review and request Word generation."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.report import Report
from app.services.document_generator import DocumentGenerator
from app.services.report_review import missing_required_fields, review_warnings
from app.ui.review_summary import review_summary


class ReviewPage(QWidget):
    changed = Signal()

    back_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.report: Report | None = None
        self.project_directory: Path | None = None
        self.before_generate: Callable[[], bool] | None = None
        self._loading = False
        self._text_fields: dict[str, QLineEdit] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        self.title = QLabel("Revisão da vistoria")
        layout.addWidget(self.title)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        complementary_box = QGroupBox("INFORMAÇÕES COMPLEMENTARES")
        form = QFormLayout(complementary_box)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        for name, label in (
            ("delivered_keys", "Chaves entregues"), ("energy_meter", "Medidor de energia"),
            ("consumer_unit", "Unidade consumidora"),
        ):
            field = QLineEdit()
            field.textChanged.connect(lambda value, name=name: self._update(name, value))
            self._text_fields[name] = field
            setattr(self, f"{name}_field", field)
            field_label = QLabel(label)
            setattr(self, f"{name}_label", field_label)
            form.addRow(field_label, field)
        self.general_notes_field = QTextEdit()
        self.general_notes_field.setAcceptRichText(False)
        self.general_notes_field.setMaximumHeight(90)
        self.general_notes_field.textChanged.connect(
            lambda: self._update("general_notes", self.general_notes_field.toPlainText())
        )
        form.addRow("Observações gerais", self.general_notes_field)
        self.issue_location_field = QLineEdit()
        self.issue_location_field.textChanged.connect(
            lambda value: self._update("issue_location", value)
        )
        self._text_fields["issue_location"] = self.issue_location_field
        form.addRow("Local de emissão", self.issue_location_field)
        content_layout.addWidget(complementary_box)
        summary_box = QGroupBox("RESUMO DA VISTORIA")
        summary_layout = QFormLayout(summary_box)
        self.summary_fields: dict[str, QLabel] = {}
        for name, label in (
            ("report_type", "Tipo da vistoria"), ("title", "Título"), ("property", "Imóvel"),
            ("address", "Endereço"), ("landlord", "Locador"), ("tenant", "Locatário"),
            ("sections", "Quantidade de ambientes"), ("photos", "Quantidade total de fotos"),
        ):
            field = QLabel()
            field.setTextFormat(Qt.TextFormat.PlainText)
            field.setWordWrap(True)
            self.summary_fields[name] = field
            summary_layout.addRow(label, field)
        content_layout.addWidget(summary_box)
        warnings_box = QGroupBox("AVISOS — NÃO IMPEDEM A GERAÇÃO")
        warnings_layout = QVBoxLayout(warnings_box)
        self.warnings_label = QLabel()
        self.warnings_label.setTextFormat(Qt.TextFormat.PlainText)
        self.warnings_label.setWordWrap(True)
        warnings_layout.addWidget(self.warnings_label)
        content_layout.addWidget(warnings_box)
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        buttons = QHBoxLayout()
        self.back_button = QPushButton("Voltar")
        self.generate_button = QPushButton("Gerar relatório Word")
        self.generate_button.setEnabled(False)
        self.back_button.clicked.connect(self.back_requested.emit)
        self.generate_button.clicked.connect(self._generate)
        buttons.addWidget(self.back_button)
        buttons.addStretch()
        buttons.addWidget(self.generate_button)
        layout.addLayout(buttons)

    def _update(self, name: str, value: str) -> None:
        if self.report is not None and not self._loading:
            target = self.report.complementary_information
            if getattr(target, name) != value:
                setattr(target, name, value)
                self.changed.emit()

    def set_report(self, report: Report, project_directory: Path | None = None) -> None:
        """Refresh widgets without changing the bound objects or a previous report."""
        self._loading = True
        try:
            self.report = report
            self.project_directory = project_directory
            information = report.complementary_information
            for name, field in self._text_fields.items():
                field.setText(getattr(information, name))
            self.general_notes_field.setPlainText(information.general_notes)
            is_initial = report.report_type == "Inicial"
            self.energy_meter_field.setVisible(is_initial)
            self.energy_meter_label.setVisible(is_initial)
            for name, value in review_summary(report).items():
                self.summary_fields[name].setText(value)
            warnings = review_warnings(report)
            self.warnings_label.setText("\n".join(warnings) if warnings else "Nenhum aviso.")
            self.generate_button.setEnabled(True)
        finally:
            self._loading = False

    def _generate(self) -> None:
        if self.report is None:
            return
        missing = missing_required_fields(self.report)
        if missing:
            QMessageBox.warning(
                self, "Campos pendentes", "Preencha os campos obrigatórios:\n" + "\n".join(missing)
            )
            return
        if self.project_directory is None:
            QMessageBox.warning(
                self, "Pasta do projeto não definida",
                "Crie ou abra uma vistoria com uma pasta do projeto antes de gerar o Word.",
            )
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar relatório Word", "relatorio-vistoria.docx", "Documento Word (*.docx)"
        )
        if not filename:
            return
        if self.before_generate is not None and not self.before_generate():
            return
        try:
            DocumentGenerator.generate(self.report, self.project_directory, Path(filename))
        except Exception:
            # Keep template, image and filesystem failures inside the UI boundary.
            QMessageBox.warning(
                self, "Não foi possível gerar o relatório",
                "Não foi possível gerar o Word. Verifique as imagens, a pasta de destino "
                "e se o arquivo está aberto em outro programa.",
            )
            return
        QMessageBox.information(self, "Relatório gerado", "Relatório Word gerado com sucesso.")
