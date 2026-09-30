"""Manage photo associations and delegate image import to PhotoService."""

from pathlib import Path

from PIL.Image import DecompressionBombError
from PySide6.QtWidgets import QFileDialog, QGroupBox, QLabel, QMessageBox, QPushButton, QVBoxLayout

from app.models.photo import Photo
from app.models.section import Section
from app.services.photo_service import PhotoService
from app.ui.photo_editor_widget import PhotoEditorWidget


class SectionPhotosWidget(QGroupBox):
    def __init__(self, section: Section, project_directory: Path | None = None) -> None:
        super().__init__("FOTOS")
        self.section = section
        self.project_directory = project_directory
        self.editors: list[PhotoEditorWidget] = []
        self.content_layout = QVBoxLayout(self)
        self.add_button = QPushButton("Adicionar foto")
        self.add_button.setEnabled(project_directory is not None)
        self.add_button.setToolTip("Selecione a pasta do projeto para importar fotos.")
        self.add_button.clicked.connect(self._add)
        self.content_layout.addWidget(self.add_button)
        self.empty_label = QLabel("Nenhuma foto adicionada neste ambiente.")
        self.content_layout.addWidget(self.empty_label)
        self.refresh()

    def refresh(self) -> None:
        for editor in self.editors:
            self.content_layout.removeWidget(editor)
            editor.hide()
            editor.deleteLater()
        self.editors = []
        for index, photo in enumerate(self.section.photos):
            editor = PhotoEditorWidget(photo, self.project_directory)
            editor.remove_requested.connect(lambda photo=photo: self._remove(photo))
            editor.move_requested.connect(lambda offset, photo=photo: self._move(photo, offset))
            editor.up_button.setEnabled(index > 0)
            editor.down_button.setEnabled(index < len(self.section.photos) - 1)
            self.editors.append(editor)
            self.content_layout.addWidget(editor)
        self.empty_label.setVisible(not self.editors)

    def _add(self) -> None:
        if self.project_directory is None:
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, "Adicionar foto", "", "Imagens (*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG)"
        )
        if not filename:
            return
        try:
            PhotoService.import_photo(Path(filename), self.project_directory, self.section)
        except (OSError, ValueError, SyntaxError, DecompressionBombError):
            QMessageBox.warning(
                self, "Não foi possível adicionar a foto",
                "Não foi possível importar a imagem. Verifique o arquivo e a pasta do projeto.",
            )
            return
        self.refresh()

    def _remove(self, photo: Photo) -> None:
        self.section.remove_photo(photo)
        self.refresh()

    def _move(self, photo: Photo, offset: int) -> None:
        self.section.move_photo(photo, offset)
        self.refresh()
