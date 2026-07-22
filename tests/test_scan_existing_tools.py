import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import scan_existing_tools as scanner  # noqa: E402


def write_skill(root: Path, name: str, description: str) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}\n---\n", encoding="utf-8")


def test_query_filters_results_instead_of_dumping_all_skills(tmp_path):
    write_skill(tmp_path, "setup-helper", "Installs verified tools")
    write_skill(tmp_path, "unrelated", "Writes fiction")
    report = scanner.scan([tmp_path], "install")
    assert [item["name"] for item in report["skills"]] == ["setup-helper"]
    assert report["errors"] == []
    assert report["truncated"] is False


def test_missing_root_is_reported_as_data_not_a_nonzero_failure(tmp_path):
    report = scanner.scan([tmp_path / "does-not-exist"], "tool")
    assert report["skills"] == []
    assert report["errors"] == [f"not a readable directory: {tmp_path / 'does-not-exist'}"]


def test_max_results_prevents_unbounded_output(tmp_path):
    for index in range(3):
        write_skill(tmp_path, f"tool-{index}", "tool support")
    report = scanner.scan([tmp_path], "tool", max_results=2)
    assert len(report["skills"]) == 2
    assert report["truncated"] is True


def test_utf8_configuration_is_safe_for_captured_output():
    scanner.configure_utf8_output()
