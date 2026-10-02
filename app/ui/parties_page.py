"""Edit the existing parties directly on the current Report."""

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models.party import Party
from app.models.report import Report
from app.services.app_paths import AppPaths
from app.services.landlord_service import (
    LANDLORD_FIELDS,
    LandlordService,
    MissingLandlordIdentityError,
)


class SavedLandlordsComboBox(QComboBox):
    about_to_show = Signal()

    def showPopup(self) -> None:
        self.about_to_show.emit()
        super().showPopup()


class PartiesPage(QWidget):
    changed = Signal()

    back_requested = Signal()
    continue_requested = Signal()

    def __init__(self, *, app_paths: AppPaths | None = None) -> None:
        super().__init__()
        self.report: Report | None = None
        self._loading = False
        self.landlord_service = LandlordService(app_paths if app_paths is not None else AppPaths())
        self._landlords: list[Party] = []
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
            if role == "landlord":
                self.landlord_selector = SavedLandlordsComboBox()
                self.landlord_selector.addItem("Selecione um locador...")
                self.landlord_selector.setEnabled(False)
                self.landlord_selector.about_to_show.connect(
                    lambda: self._refresh_landlords(notify=True)
                )
                self.landlord_selector.currentIndexChanged.connect(self._select_landlord)
                form.addRow("Locador salvo", self.landlord_selector)
            for name, label in (
                ("name", "Nome"), ("document", "CPF / CNPJ"), ("phone", "Telefone"),
                ("email", "E-mail"), ("address", "Endereço"),
            ):
                field = QLineEdit()
                if name == "document":
                    field.setPlaceholderText("Ex.: 123.456.789-00 ou 12.345.678/0001-90")
                elif name == "phone":
                    field.setPlaceholderText("Ex.: (21) 99999-9999")
                field.textChanged.connect(
                    lambda value, role=role, name=name: self._update(role, name, value)
                )
                self._text_fields[role, name] = field
                setattr(self, f"{role}_{name}_field", field)
                form.addRow(label, field)
            if role == "landlord":
                agenda_buttons = QHBoxLayout()
                self.save_landlord_button = QPushButton("Salvar locador")
                self.save_landlord_button.setEnabled(False)
                self.save_landlord_button.clicked.connect(self._save_landlord)
                self.delete_landlord_button = QPushButton("Excluir locador salvo")
                self.delete_landlord_button.setEnabled(False)
                self.delete_landlord_button.clicked.connect(self._delete_landlord)
                agenda_buttons.addWidget(self.save_landlord_button)
                agenda_buttons.addWidget(self.delete_landlord_button)
                form.addRow(agenda_buttons)
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
        self.landlord_selector.setEnabled(True)
        self.save_landlord_button.setEnabled(True)
        self._refresh_landlords()

    def _agenda_error(self) -> None:
        QMessageBox.warning(
            self, "Agenda de locadores indisponível",
            "Não foi possível acessar a agenda de locadores. Verifique se o arquivo está "
            "disponível e válido e se você tem permissão para acessá-lo. "
            "Nenhum cadastro foi substituído.",
        )

    def _refresh_landlords(self, *, notify: bool = False) -> None:
        try:
            landlords = self.landlord_service.list_landlords()
        except (OSError, ValueError):
            landlords = []
            if notify:
                self._agenda_error()
        self._landlords = landlords
        with QSignalBlocker(self.landlord_selector):
            self.landlord_selector.clear()
            self.landlord_selector.addItem("Selecione um locador...")
            for landlord in landlords:
                self.landlord_selector.addItem(
                    f"{landlord.name or 'Sem nome'} — {landlord.document}"
                    if landlord.document else landlord.name or "Sem nome"
                )
        self.delete_landlord_button.setEnabled(False)

    def _select_landlord(self, index: int) -> None:
        self.delete_landlord_button.setEnabled(index > 0)
        if self.report is None or index <= 0 or index > len(self._landlords):
            return
        try:
            self.landlord_service.list_landlords()
        except (OSError, ValueError):
            self._agenda_error()
            return
        saved = self._landlords[index - 1]
        modified = self.report.landlord != saved
        self._loading = True
        try:
            for name in LANDLORD_FIELDS:
                value = getattr(saved, name)
                setattr(self.report.landlord, name, value)
                self._text_fields["landlord", name].setText(value)
        finally:
            self._loading = False
        if modified:
            self.changed.emit()

    def _save_landlord(self) -> None:
        if self.report is None:
            return
        try:
            self.landlord_service.save(self.report.landlord)
        except MissingLandlordIdentityError as error:
            QMessageBox.warning(self, "Locador não identificado", str(error))
            return
        except (OSError, ValueError):
            self._agenda_error()
            return
        self._refresh_landlords()
        QMessageBox.information(self, "Locador salvo", "Locador salvo na agenda.")

    def _delete_landlord(self) -> None:
        index = self.landlord_selector.currentIndex()
        if index <= 0 or index > len(self._landlords):
            return
        choice = QMessageBox.question(
            self, "Excluir locador salvo",
            "Excluir este locador da agenda? Os dados das vistorias serão mantidos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        try:
            self.landlord_service.delete(self._landlords[index - 1])
        except (OSError, ValueError):
            self._agenda_error()
            return
        self._refresh_landlords()
