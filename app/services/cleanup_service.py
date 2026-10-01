"""Apply manual retention to managed projects, refusing suspicious filesystem trees."""

import json
import os
import shutil
import stat
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from app.services.app_paths import AppPaths
from app.services.project_service import ProjectService


@dataclass
class CleanupResult:
    moved_to_trash: list[Path] = field(default_factory=list)
    deleted: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    errors: dict[Path, str] = field(default_factory=dict)


def _is_link(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def _safe_child(path: Path, root: Path) -> bool:
    """Require a real direct child; lexical discovery alone is insufficient."""
    return (not _is_link(root) and root.is_dir()
            and not _is_link(path) and path.is_dir()
            and path.resolve(strict=True).parent == root.resolve(strict=True))


def _safe_tree(directory: Path) -> bool:
    """Reject links/reparse points anywhere, including files used for validation."""
    resolved = directory.resolve(strict=True)

    def fail(error: OSError) -> None:
        raise error

    for current, directories, files in os.walk(directory, followlinks=False, onerror=fail):
        for name in directories + files:
            path = Path(current) / name
            if _is_link(path) or not path.resolve(strict=True).is_relative_to(resolved):
                return False
    return True


def _metadata(directory: Path, now: datetime) -> None:
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                prefix=".cleanup-", suffix=".tmp", delete=False) as file:
            temporary = Path(file.name)
            json.dump({"trashed_at": now.isoformat()}, file)
        temporary.replace(directory / ".cleanup.json")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _trashed_at(directory: Path) -> datetime:
    with (directory / ".cleanup.json").open(encoding="utf-8") as file:
        data = json.load(file)
    value = datetime.fromisoformat(data["trashed_at"])
    if value.utcoffset() is None:
        raise ValueError("Trash timestamp must include timezone")
    return value.astimezone(UTC)


class CleanupService:
    @staticmethod
    def run(app_paths: AppPaths, *, now: datetime | None = None,
            current_project: Path | None = None) -> CleanupResult:
        now = now if now is not None else datetime.now(UTC)
        if now.utcoffset() is None:
            raise ValueError("now must include timezone")
        now = now.astimezone(UTC)
        # Refuse redirected storage roots before creating any directories.
        for root in (app_paths.app_root, app_paths.projects_root, app_paths.trash_root):
            if (root.exists() or root.is_symlink()) and _is_link(root):
                raise ValueError("Unsafe storage root")
        app_paths.ensure_directories()
        for root in (app_paths.projects_root, app_paths.trash_root):
            if root.resolve(strict=True).parent != app_paths.app_root.resolve(strict=True):
                raise ValueError("Storage root outside application directory")
        current = current_project.resolve() if current_project is not None else None
        result = CleanupResult()
        # Snapshot trash first, so newly moved projects are never deleted in this run.
        trash_items = sorted(app_paths.trash_root.iterdir())
        for directory in sorted(app_paths.projects_root.iterdir()):
            metadata_created = False
            moved = False
            try:
                if (not _safe_child(directory, app_paths.projects_root)
                        or directory.resolve() == current or not _safe_tree(directory)):
                    result.skipped.append(directory)
                    continue
                report = ProjectService.load(directory)
                modified = datetime.fromtimestamp((directory / "projeto.json").stat().st_mtime, UTC)
                if report.protected_from_cleanup or now - modified < timedelta(days=7):
                    result.skipped.append(directory)
                    continue
                if (not _safe_child(directory, app_paths.projects_root)
                        or _is_link(app_paths.trash_root)):
                    result.skipped.append(directory)
                    continue
                destination = app_paths.trash_root / directory.name
                while destination.exists() or destination.is_symlink():
                    destination = app_paths.trash_root / f"{directory.name}-{uuid4().hex}"
                _metadata(directory, now)
                metadata_created = True
                # Revalidate after reads/writes, immediately before the filesystem mutation.
                if (not _safe_child(directory, app_paths.projects_root)
                        or not _safe_tree(directory)
                        or _is_link(app_paths.trash_root)
                        or destination.parent.resolve() != app_paths.trash_root.resolve()
                        or destination.exists() or destination.is_symlink()):
                    result.skipped.append(directory)
                    continue
                directory.rename(destination)
                moved = True
                result.moved_to_trash.append(destination)
            except Exception as error:
                result.errors[directory] = type(error).__name__
            finally:
                if metadata_created and not moved:
                    try:
                        if (not _safe_child(directory, app_paths.projects_root)
                                or not _safe_tree(directory)):
                            raise ValueError("Unsafe metadata cleanup path")
                        (directory / ".cleanup.json").unlink(missing_ok=True)
                    except Exception as cleanup_error:
                        original = result.errors.get(directory, "Move skipped")
                        result.errors[directory] = (
                            f"{original}; metadata cleanup: {type(cleanup_error).__name__}"
                        )
        for directory in trash_items:
            try:
                if (not _safe_child(directory, app_paths.trash_root)
                        or directory.resolve() == current or not _safe_tree(directory)):
                    result.skipped.append(directory)
                    continue
                report = ProjectService.load(directory)
                if report.protected_from_cleanup:
                    result.skipped.append(directory)
                    continue
                if now - _trashed_at(directory) < timedelta(days=30):
                    result.skipped.append(directory)
                    continue
                if not _safe_child(directory, app_paths.trash_root) or not _safe_tree(directory):
                    result.skipped.append(directory)
                    continue
                shutil.rmtree(directory)
                result.deleted.append(directory)
            except Exception as error:
                result.errors[directory] = type(error).__name__
        return result
