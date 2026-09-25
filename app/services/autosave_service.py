"""Track pending changes and delegate explicit save attempts to ProjectService."""

from pathlib import Path

from app.models.report import Report
from app.services.project_service import ProjectService


class AutosaveService:
    """Track unsaved changes for one report without scheduling or file I/O."""

    def __init__(self) -> None:
        self._dirty = False

    @property
    def is_dirty(self) -> bool:
        """Return whether changes are pending."""
        return self._dirty

    def mark_dirty(self) -> None:
        """Mark the report as having unsaved changes."""
        self._dirty = True

    def save_if_needed(self, report: Report, project_directory: Path) -> None:
        """Save pending changes, clearing dirty only after successful persistence."""
        if not self._dirty:
            return
        ProjectService.save(report, project_directory)
        self._dirty = False
