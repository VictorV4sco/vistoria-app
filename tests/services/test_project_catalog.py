import os
from datetime import date

from app.models.report import Report
from app.services.project_catalog import ProjectCatalogService
from app.services.project_service import ProjectService


def test_catalog_only_valid_direct_children_sorted_by_activity(tmp_path):
    root = tmp_path / "Projetos"
    first, second = root / "first", root / "second"
    ProjectService.save(Report(title="Casa", report_type="Final",
                               inspection_date=date(2026, 10, 1)), first)
    ProjectService.save(Report(), second)
    # Separate activity by a day so coarse filesystem timestamps preserve the order.
    older = 1_700_000_000
    newer = older + 86_400
    os.utime(first / "projeto.json", (older, older))
    os.utime(second / "projeto.json", (newer, newer))
    (root / "file.txt").write_text("ignored")
    (root / "invalid").mkdir()
    (root / "invalid" / "projeto.json").write_text("broken")
    ProjectService.save(Report(), root / "container" / "nested")
    outside = tmp_path / "outside"
    ProjectService.save(Report(), outside)
    (root / "linked").symlink_to(outside, target_is_directory=True)
    entries = ProjectCatalogService.list_projects(root)
    assert [entry.directory for entry in entries] == [second, first]
    assert "Casa" in entries[1].label
    assert "Final" in entries[1].label
    assert "01/10/2026" in entries[1].label
    assert "second" in entries[0].label


def test_equal_activity_has_predictable_folder_order(tmp_path):
    for name in ("b", "a"):
        ProjectService.save(Report(), tmp_path / name)
        os.utime(tmp_path / name / "projeto.json", ns=(10, 10))
    assert [e.directory.name for e in ProjectCatalogService.list_projects(tmp_path)] == ["a", "b"]
