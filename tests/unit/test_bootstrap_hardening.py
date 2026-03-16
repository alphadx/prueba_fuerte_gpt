import json
import subprocess
from pathlib import Path


def test_bootstrap_report_validator_and_stability(tmp_path: Path) -> None:
    report_path = tmp_path / "bootstrap_report.json"

    run_bootstrap = subprocess.run(
        [
            "python3",
            "infra/scripts/bootstrap_test_state.py",
            "--max-seconds",
            "600",
            "--report-path",
            str(report_path),
            "--retries",
            "1",
            "--step-timeout-seconds",
            "240",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run_bootstrap.returncode == 0, run_bootstrap.stderr

    run_validate = subprocess.run(
        [
            "python3",
            "infra/scripts/validate_bootstrap_report.py",
            "--path",
            str(report_path),
            "--max-seconds",
            "600",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run_validate.returncode == 0, run_validate.stderr

    stability_output = tmp_path / "stability.json"
    run_stability = subprocess.run(
        [
            "python3",
            "infra/scripts/bootstrap_stability.py",
            "--runs",
            "1",
            "--min-success-rate",
            "95",
            "--max-seconds",
            "600",
            "--output",
            str(stability_output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run_stability.returncode == 0, run_stability.stderr

    payload = json.loads(stability_output.read_text(encoding="utf-8"))
    assert payload["runs"] == 1
    assert payload["passes_threshold"] is True
