"""Initial desktop flow for starting an inspection in memory."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QLabel,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.models.report import Report


class MainWindow(QMainWindow):
    """Choose an inspection type and open its temporary next page."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VistoriaApp")
        self.resize(560, 360)
        self.report: Report | None = None

        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)
        self.start_page = QWidget()
        self.placeholder_page = QWidget()
        self.pages.addWidget(self.start_page)
        self.pages.addWidget(self.placeholder_page)

        start_layout = QVBoxLayout(self.start_page)
        start_layout.setContentsMargins(32, 32, 32, 32)
        start_layout.setSpacing(16)
        title = QLabel("VistoriaApp")
        title_font = title.font()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        start_layout.addWidget(title)
        start_layout.addWidget(QLabel("Nova vistoria"))

        type_box = QGroupBox("Tipo da vistoria:")
        type_layout = QVBoxLayout(type_box)
        self.initial_radio = QRadioButton("Vistoria Inicial")
        self.final_radio = QRadioButton("Vistoria Final")
        self.type_group = QButtonGroup(self)
        self.type_group.setExclusive(True)
        for radio in (self.initial_radio, self.final_radio):
            self.type_group.addButton(radio)
            type_layout.addWidget(radio, alignment=Qt.AlignmentFlag.AlignLeft)
        self.initial_radio.setChecked(True)
        start_layout.addWidget(type_box)
        start_layout.addStretch()
        self.continue_button = QPushButton("Continuar")
        self.continue_button.clicked.connect(self._start_inspection)
        start_layout.addWidget(self.continue_button, alignment=Qt.AlignmentFlag.AlignRight)

        placeholder_layout = QVBoxLayout(self.placeholder_page)
        placeholder_layout.setContentsMargins(32, 32, 32, 32)
        self.placeholder_title = QLabel()
        self.placeholder_title.setWordWrap(True)
        placeholder_layout.addWidget(self.placeholder_title)
        placeholder_layout.addStretch()
        self.back_button = QPushButton("Voltar")
        self.back_button.clicked.connect(self._show_start)
        placeholder_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)

    def _start_inspection(self) -> None:
        report_type = "Inicial" if self.initial_radio.isChecked() else "Final"
        self.report = Report(report_type=report_type)
        self.placeholder_title.setText(f"Nova Vistoria {self.report.report_type}")
        self.pages.setCurrentWidget(self.placeholder_page)
        self.back_button.setFocus()

    def _show_start(self) -> None:
        self.pages.setCurrentWidget(self.start_page)
        self.continue_button.setFocus()
