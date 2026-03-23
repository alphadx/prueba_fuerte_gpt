import subprocess
from pathlib import Path


def test_smoke_test_state_passes_with_generated_inputs(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed.json"
    fixtures_path = tmp_path / "fixtures.json"

    run_seed = subprocess.run(
        ["python3", "infra/scripts/seed.py", "--output", str(seed_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run_seed.returncode == 0, run_seed.stderr

    run_fixtures = subprocess.run(
        ["python3", "infra/scripts/load_fixtures.py", "--output", str(fixtures_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run_fixtures.returncode == 0, run_fixtures.stderr

    run_smoke = subprocess.run(
        [
            "python3",
            "infra/scripts/smoke_test_state.py",
            "--seed-path",
            str(seed_path),
            "--fixtures-path",
            str(fixtures_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run_smoke.returncode == 0, run_smoke.stderr
    assert "[smoke] OK: estado QA ejecutable" in run_smoke.stdout
