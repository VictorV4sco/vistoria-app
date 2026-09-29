"""Generate Word reports from the official presentation template."""

from pathlib import Path
from tempfile import TemporaryDirectory

from docx.shared import Cm
from docxtpl import DocxTemplate, InlineImage

from app.models.report import Report
from app.services.image_service import ImageService

TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "modelo_relatorio.docx"


class DocumentGenerator:
    @staticmethod
    def generate(report: Report, project_directory: Path, destination: Path) -> None:
        """Publish a rendered document only after its temporary save succeeds.

        The destination's parent directory must exist. Template and I/O errors
        propagate, preserving an existing destination and cleaning temporary files.
        Images are read from project_directory and optimized without changing originals.
        """
        template = DocxTemplate(TEMPLATE_PATH)
        sections = []
        photo_number = 0
        for section in report.sections:
            photos = []
            for photo in section.photos:
                optimized = ImageService.optimize_for_report(
                    Path(photo.file_path), project_directory
                )
                photo_number += 1
                photos.append({
                    "image": InlineImage(template, str(project_directory / optimized), width=Cm(7)),
                    "number": photo_number,
                    "caption": photo.caption,
                })
            sections.append({
                "name": section.name,
                "description": section.description,
                "notes": section.notes,
                "photo_rows": [photos[index:index + 2] for index in range(0, len(photos), 2)],
            })
        context = {
            "title": report.title,
            "report_type": report.report_type,
            "code": report.code,
            "inspection_date": (
                report.inspection_date.strftime("%d/%m/%Y")
                if report.inspection_date is not None else ""
            ),
            "inspector_name": report.inspector_name,
            "issue_date": (
                report.issue_date.strftime("%d/%m/%Y")
                if report.issue_date is not None else ""
            ),
            "property": report.property,
            "landlord": report.landlord,
            "tenant": report.tenant,
            "sections": sections,
        }
        template.render(context, autoescape=True)
        with TemporaryDirectory(prefix=".document-", dir=destination.parent) as directory:
            temporary = Path(directory) / "report.docx"
            template.save(temporary)
            temporary.replace(destination)
