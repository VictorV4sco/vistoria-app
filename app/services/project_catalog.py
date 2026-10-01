"""Discover valid local projects directly inside the managed projects root."""

from dataclasses import dataclass
from pathlib import Path

from app.services.project_service import ProjectService


@dataclass(frozen=True)
class ProjectEntry:
    directory: Path
    label: str
    modified_ns: int


class ProjectCatalogService:
    @staticmethod
    def list_projects(projects_root: Path) -> list[ProjectEntry]:
        entries = []
        for directory in projects_root.iterdir():
            if directory.is_symlink() or not directory.is_dir():
                continue
            try:
                if (directory / "projeto.json").is_symlink():
                    continue
                report = ProjectService.load(directory)
                modified = (directory / "projeto.json").stat().st_mtime_ns
            except (OSError, ValueError, KeyError, TypeError):
                continue
            inspection_date = (
                report.inspection_date.strftime("%d/%m/%Y")
                if report.inspection_date else "Sem data"
            )
            label = (f"{report.title or directory.name} — {report.report_type} — "
                     f"{inspection_date} ({directory.name})")
            entries.append(ProjectEntry(directory, label, modified))
        return sorted(entries, key=lambda entry: (-entry.modified_ns, entry.directory.name))
