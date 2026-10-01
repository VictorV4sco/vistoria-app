import json
import os
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from app.models.report import Report
from app.services.app_paths import AppPaths
from app.services.cleanup_service import CleanupService
from app.services.project_service import ProjectService

NOW = datetime(2026, 10, 1, tzinfo=UTC)


@pytest.fixture
def paths(tmp_path):
    paths = AppPaths(tmp_path / "app")
    paths.ensure_directories()
    return paths


def project(root, name, days, protected=False):
    directory = root / name
    ProjectService.save(Report(protected_from_cleanup=protected), directory)
    stamp = (NOW - timedelta(days=days)).timestamp()
    os.utime(directory / "projeto.json", (stamp, stamp))
    return directory


def trash(paths, name, days, protected=False):
    directory = project(paths.trash_root, name, 100, protected)
    (directory / ".cleanup.json").write_text(json.dumps({
        "trashed_at": (NOW - timedelta(days=days)).isoformat()
    }))
    return directory


@pytest.mark.parametrize("days,moved", [(6.999, False), (7, True), (8, True)])
def test_seven_day_boundary(paths, days, moved):
    directory = project(paths.projects_root, "inspection", days)
    result = CleanupService.run(paths, now=NOW)
    assert directory.exists() == (not moved)
    assert len(result.moved_to_trash) == int(moved)
    assert not result.errors


def test_whole_project_and_fresh_metadata(paths):
    directory = project(paths.projects_root, "old", 100)
    for name in ("projeto.backup.json", "imagens/originals/photo.png",
                 "imagens/optimized/photo.jpg", "relatorios/report.docx"):
        file = directory / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"keep")
    result = CleanupService.run(paths, now=NOW)
    destination = result.moved_to_trash[0]
    for name in ("projeto.backup.json", "imagens/originals/photo.png",
                 "imagens/optimized/photo.jpg", "relatorios/report.docx"):
        assert (destination / name).read_bytes() == b"keep"
    metadata = json.loads((destination / ".cleanup.json").read_text())
    stamp = datetime.fromisoformat(metadata["trashed_at"])
    assert stamp == NOW
    assert stamp.utcoffset() == timedelta(0)
    assert destination.exists()
    assert not result.deleted


def test_protected_current_and_corrupt_stay(paths):
    protected = project(paths.projects_root, "protected", 20, True)
    current = project(paths.projects_root, "current", 20)
    corrupt = project(paths.projects_root, "corrupt", 20)
    (corrupt / "projeto.json").write_text("broken")
    result = CleanupService.run(paths, now=NOW, current_project=current)
    assert all(d.exists() for d in (protected, current, corrupt))
    assert not result.moved_to_trash
    assert protected in result.skipped
    assert current in result.skipped
    assert corrupt in result.errors


def test_collision_preserves_destination(paths):
    project(paths.projects_root, "same", 10)
    existing = trash(paths, "same", 1)
    (existing / "keep.txt").write_text("keep")
    result = CleanupService.run(paths, now=NOW)
    assert len(result.moved_to_trash) == 1
    assert result.moved_to_trash[0] != existing
    assert result.moved_to_trash[0].name.startswith("same-")
    assert (existing / "keep.txt").read_text() == "keep"


@pytest.mark.parametrize("days,deleted", [(29.999, False), (30, True), (31, True)])
def test_thirty_day_boundary(paths, days, deleted):
    directory = trash(paths, "old", days)
    result = CleanupService.run(paths, now=NOW)
    assert directory.exists() == (not deleted)
    assert result.deleted == ([directory] if deleted else [])


@pytest.mark.parametrize("metadata", [None, "broken", '{}', '{"trashed_at":"invalid"}',
                                     '{"trashed_at":"2020-01-01T00:00:00"}'])
def test_invalid_metadata_never_deletes(paths, metadata):
    directory = project(paths.trash_root, "old", 100)
    if metadata is not None:
        (directory / ".cleanup.json").write_text(metadata)
    result = CleanupService.run(paths, now=NOW)
    assert directory.exists()
    assert not result.deleted
    assert directory in result.errors or directory in result.skipped


def test_protected_and_corrupt_trash_never_deleted(paths):
    protected = trash(paths, "protected", 40, True)
    corrupt = trash(paths, "corrupt", 40)
    (corrupt / "projeto.json").write_text("broken")
    result = CleanupService.run(paths, now=NOW)
    assert protected.exists() and corrupt.exists()
    assert not result.deleted


def test_symlinks_files_and_nested_projects_ignored(paths, tmp_path, monkeypatch):
    outside = project(tmp_path, "outside", 100)
    (paths.projects_root / "link").symlink_to(outside, target_is_directory=True)
    (paths.trash_root / "link").symlink_to(outside, target_is_directory=True)
    project(paths.projects_root / "container", "nested", 100)
    (paths.projects_root / "file.txt").write_text("keep")
    remove = Mock()
    monkeypatch.setattr("shutil.rmtree", remove)
    result = CleanupService.run(paths, now=NOW)
    assert outside.exists()
    assert (paths.projects_root / "container" / "nested").exists()
    assert not result.moved_to_trash
    remove.assert_not_called()


def test_symlink_inside_project_is_suspicious(paths, tmp_path, monkeypatch):
    directory = trash(paths, "old", 40)
    outside = tmp_path / "outside"
    outside.mkdir()
    (directory / "imagens").symlink_to(outside, target_is_directory=True)
    remove = Mock()
    monkeypatch.setattr("shutil.rmtree", remove)
    result = CleanupService.run(paths, now=NOW)
    assert directory in result.skipped
    remove.assert_not_called()
    assert outside.exists()


def test_resolved_outside_path_never_reaches_delete(paths, tmp_path, monkeypatch):
    directory = trash(paths, "old", 40)
    original = type(directory).resolve
    monkeypatch.setattr(type(directory), "resolve", lambda self, *a, **kw:
                        tmp_path / "outside" if self == directory else original(self, *a, **kw))
    remove = Mock()
    monkeypatch.setattr("shutil.rmtree", remove)
    CleanupService.run(paths, now=NOW)
    remove.assert_not_called()


@pytest.mark.parametrize("operation", ["move", "delete"])
def test_item_errors_do_not_interrupt_others(paths, monkeypatch, operation):
    root = paths.projects_root if operation == "move" else paths.trash_root
    bad = project(root, "bad", 40) if operation == "move" else trash(paths, "bad", 40)
    good = project(root, "good", 40) if operation == "move" else trash(paths, "good", 40)
    if operation == "move":
        from pathlib import Path
        original = Path.rename
        def fail(self, destination):
            if self == bad:
                raise PermissionError("denied")
            return original(self, destination)
        monkeypatch.setattr(Path, "rename", fail)
    else:
        import shutil
        original = shutil.rmtree
        def fail(path):
            if path == bad:
                raise PermissionError("denied")
            original(path)
        monkeypatch.setattr(shutil, "rmtree", fail)
    result = CleanupService.run(paths, now=NOW)
    assert bad in result.errors
    assert bad.exists()
    assert not good.exists()
    assert len(result.moved_to_trash if operation == "move" else result.deleted) == 1


def test_reparse_point_never_reaches_delete(paths, monkeypatch):
    from types import SimpleNamespace

    directory = trash(paths, "junction", 40)
    original = type(directory).lstat

    def attributes(self, *args, **kwargs):
        if self == directory:
            return SimpleNamespace(st_mode=original(self).st_mode, st_file_attributes=0x400)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(type(directory), "lstat", attributes)
    remove = Mock()
    monkeypatch.setattr("shutil.rmtree", remove)
    result = CleanupService.run(paths, now=NOW)
    assert directory in result.skipped
    remove.assert_not_called()


def test_redirected_root_is_rejected_before_operations(tmp_path, monkeypatch):
    paths = AppPaths(tmp_path / "app")
    paths.app_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    paths.projects_root.symlink_to(outside, target_is_directory=True)
    remove = Mock()
    monkeypatch.setattr("shutil.rmtree", remove)
    with pytest.raises(ValueError, match="Unsafe storage root"):
        CleanupService.run(paths, now=NOW)
    assert not paths.trash_root.exists()
    remove.assert_not_called()


def test_naive_now_is_rejected(paths):
    with pytest.raises(ValueError, match="timezone"):
        CleanupService.run(paths, now=NOW.replace(tzinfo=None))


def test_root_replaced_during_validation_cannot_move_external_project(paths, tmp_path, monkeypatch):
    project(paths.projects_root, "old", 40)
    outside = tmp_path / "outside"
    external = project(outside, "old", 40)
    original = ProjectService.load

    def replace_root(directory):
        report = original(directory)
        paths.projects_root.rename(paths.app_root / "original-projects")
        paths.projects_root.symlink_to(outside, target_is_directory=True)
        return report

    monkeypatch.setattr(ProjectService, "load", replace_root)
    result = CleanupService.run(paths, now=NOW)
    assert external.exists()
    assert not (external / ".cleanup.json").exists()
    assert not result.moved_to_trash


def test_failed_move_removes_trash_metadata_and_continues(paths, monkeypatch):
    from pathlib import Path

    bad = project(paths.projects_root, "bad", 40)
    good = project(paths.projects_root, "good", 40)
    original = Path.rename

    def fail(self, destination):
        if self == bad:
            assert (self / ".cleanup.json").is_file()
            raise PermissionError("move failed")
        return original(self, destination)

    monkeypatch.setattr(Path, "rename", fail)
    result = CleanupService.run(paths, now=NOW)
    assert bad.is_dir()
    assert not (bad / ".cleanup.json").exists()
    assert bad in result.errors
    assert not good.exists()
    assert result.moved_to_trash == [paths.trash_root / "good"]
    assert not result.deleted


def test_metadata_cleanup_failure_is_recorded_and_never_deletes_active_project(paths, monkeypatch):
    from pathlib import Path

    bad = project(paths.projects_root, "bad", 40)
    project(paths.projects_root, "good", 40)
    original_rename = Path.rename
    original_unlink = Path.unlink

    def fail_move(self, destination):
        if self == bad:
            raise PermissionError("move failed")
        return original_rename(self, destination)

    def fail_cleanup(self, *args, **kwargs):
        if self == bad / ".cleanup.json":
            raise OSError("cleanup failed")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "rename", fail_move)
    monkeypatch.setattr(Path, "unlink", fail_cleanup)
    remove = Mock()
    monkeypatch.setattr("shutil.rmtree", remove)
    result = CleanupService.run(paths, now=NOW)
    assert bad.exists()
    assert "PermissionError" in result.errors[bad]
    assert "OSError" in result.errors[bad]
    assert len(result.moved_to_trash) == 1
    assert not result.deleted
    remove.assert_not_called()
