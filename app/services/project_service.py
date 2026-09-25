"""Save and load a report in a local project directory."""

import json
from pathlib import Path

from app.models.report import Report
from app.services.report_serialization import report_from_dict, report_to_dict


class ProjectService:
    """Persist reports atomically, propagating I/O and decoding errors."""

    @staticmethod
    def save(report: Report, project_directory: Path) -> None:
        """Replace the project after writing it fully, keeping its previous bytes.

        Promote the new project before replacing the backup. If backup promotion
        fails, the new project and old backup remain, with the previous project
        in projeto.backup.tmp. Errors propagate without removing temporary files.
        """
        data = report_to_dict(report)
        project_directory.mkdir(parents=True, exist_ok=True)
        project = project_directory / "projeto.json"
        temporary = project_directory / "projeto.tmp"
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        backup_temporary = None
        if project.exists():
            backup_temporary = project_directory / "projeto.backup.tmp"
            backup_temporary.write_bytes(project.read_bytes())

        temporary.replace(project)
        if backup_temporary is not None:
            backup_temporary.replace(project_directory / "projeto.backup.json")

    @staticmethod
    def load(project_directory: Path) -> Report:
        """Read projeto.json and reconstruct the report using its stored values."""
        with (project_directory / "projeto.json").open(encoding="utf-8") as file:
            data = json.load(file)
        return report_from_dict(data)

    @staticmethod
    def has_valid_backup(project_directory: Path) -> bool:
        """Check whether the backup can be reconstructed, without modifying files."""
        try:
            ProjectService.load_backup(project_directory)
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            # ValueError includes JSONDecodeError and UnicodeDecodeError.
            return False
        return True

    @staticmethod
    def load_backup(project_directory: Path) -> Report:
        """Read only the backup, propagating file and reconstruction errors."""
        with (project_directory / "projeto.backup.json").open(encoding="utf-8") as file:
            data = json.load(file)
        return report_from_dict(data)

    @staticmethod
    def restore_backup(project_directory: Path) -> None:
        """Validate and atomically restore the backup, leaving the backup untouched.

        Errors propagate and may leave projeto.tmp; no automatic recovery or
        cleanup is performed.
        """
        report = ProjectService.load_backup(project_directory)
        data = report_to_dict(report)
        temporary = project_directory / "projeto.tmp"
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        temporary.replace(project_directory / "projeto.json")
