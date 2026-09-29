"""Generate Word reports from the official presentation template."""

from pathlib import Path
from tempfile import TemporaryDirectory

from docxtpl import DocxTemplate

from app.models.report import Report

TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "modelo_relatorio.docx"


class DocumentGenerator:
    @staticmethod
    def generate(report: Report, project_directory: Path, destination: Path) -> None:
        """Publish a rendered document only after its temporary save succeeds.

        The destination's parent directory must exist. Template and I/O errors
        propagate, preserving an existing destination and cleaning temporary files.
        project_directory is reserved for images in a later stage.
        """
        template = DocxTemplate(TEMPLATE_PATH)
        context = {
            "title": report.title,
            "report_type": report.report_type,
            "inspection_date": (
                report.inspection_date.strftime("%d/%m/%Y")
                if report.inspection_date is not None else ""
            ),
            "inspector_name": report.inspector_name,
        }
        template.render(context, autoescape=True)
        with TemporaryDirectory(prefix=".document-", dir=destination.parent) as directory:
            temporary = Path(directory) / "report.docx"
            template.save(temporary)
            temporary.replace(destination)
