"""Save and load a report in a local project directory."""

import json
from pathlib import Path

from app.models.report import Report
from app.services.report_serialization import report_from_dict, report_to_dict


class ProjectService:
    """Persist projeto.json directly, propagating I/O and decoding errors."""

    @staticmethod
    def save(report: Report, project_directory: Path) -> None:
        """Create the directory and overwrite projeto.json with the report data."""
        data = report_to_dict(report)
        project_directory.mkdir(parents=True, exist_ok=True)
        with (project_directory / "projeto.json").open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    @staticmethod
    def load(project_directory: Path) -> Report:
        """Read projeto.json and reconstruct the report using its stored values."""
        with (project_directory / "projeto.json").open(encoding="utf-8") as file:
            data = json.load(file)
        return report_from_dict(data)
