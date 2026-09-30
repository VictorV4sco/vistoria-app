"""Preview and edit one existing Photo without modifying its image file."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from app.models.photo import Photo


class PhotoEditorWidget(QGroupBox):
    remove_requested = Signal()
    move_requested = Signal(int)

    def __init__(self, photo: Photo, project_directory: Path | None = None) -> None:
        super().__init__("Foto")
        self.photo = photo
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.preview = QLabel("Preview indisponível")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if project_directory is not None:
            project = project_directory.resolve()
            relative = Path(photo.file_path)
            source = (project / relative).resolve()
            if not relative.is_absolute() and source.is_relative_to(project):
                pixmap = QPixmap(str(source))
                if not pixmap.isNull():
                    self.preview.setPixmap(pixmap.scaled(
                        180, 120, Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    ))
        row.addWidget(self.preview)
        caption = QVBoxLayout()
        caption.addWidget(QLabel("Legenda"))
        self.caption_field = QLineEdit(photo.caption)
        self.caption_field.textChanged.connect(lambda value: setattr(photo, "caption", value))
        caption.addWidget(self.caption_field)
        row.addLayout(caption)
        layout.addLayout(row)
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
