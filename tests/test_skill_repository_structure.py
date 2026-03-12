from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_skill_distribution_files_exist():
    skill_root = ROOT / "skills" / "onelap-strava-sync"
    assert skill_root.is_dir()
    assert (skill_root / "SKILL.md").is_file()
    assert (skill_root / "resources").is_dir()
    assert (skill_root / "resources" / "commands.md").is_file()
