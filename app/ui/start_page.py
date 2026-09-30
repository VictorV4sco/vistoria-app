"""Inspection type selection."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class StartPage(QWidget):
    continue_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        start_layout = QVBoxLayout(self)
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
        start_layout.addWidget(QLabel(
            "Continuar inicia uma nova vistoria e substitui o preenchimento atual."
        ))
        start_layout.addStretch()
        self.continue_button = QPushButton("Continuar")
        self.continue_button.clicked.connect(self.continue_requested.emit)
        start_layout.addWidget(self.continue_button, alignment=Qt.AlignmentFlag.AlignRight)

