"""Placeholder for inspection review."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ReviewPage(QWidget):
    back_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        self.title = QLabel("Revisão da vistoria")
        layout.addWidget(self.title)
        layout.addStretch()
        self.back_button = QPushButton("Voltar")
        self.back_button.clicked.connect(self.back_requested.emit)
        layout.addWidget(self.back_button)
