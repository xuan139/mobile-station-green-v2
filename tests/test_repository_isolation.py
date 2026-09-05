from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_source_has_no_bxsj_modules_or_imports() -> None:
    source_root = ROOT / "src"
    paths = [path for path in source_root.rglob("*") if path.is_file()]
    assert not any("bxsj" in path.name.lower() for path in paths)
    for path in paths:
        if path.suffix == ".py":
            assert "import bxsj" not in path.read_text(encoding="utf-8").lower()


def test_expected_module_boundaries_exist() -> None:
    package = ROOT / "src" / "green_v2"
    expected = {
        "domain",
        "application",
        "api",
        "data_access",
        "messaging",
        "ingestion",
        "parser",
        "station_agent",
        "workers",
    }
    actual = {path.name for path in package.iterdir() if path.is_dir()}
    assert expected <= actual

