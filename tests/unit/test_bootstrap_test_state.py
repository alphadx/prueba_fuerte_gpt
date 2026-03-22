import json
import subprocess
from pathlib import Path


def test_bootstrap_test_state_generates_success_report(tmp_path: Path) -> None:
    report_path = tmp_path / "bootstrap_report.json"

    run = subprocess.run(
        [
            "python3",
            "infra/scripts/bootstrap_test_state.py",
            "--max-seconds",
            "600",
            "--report-path",
            str(report_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stderr
    assert report_path.exists()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["all_steps_passed"] is True
    assert payload["within_target"] is True
    assert payload["total_seconds"] <= 600

    step_names = [item["name"] for item in payload["steps"]]
    assert step_names == [
        "seed",
        "seed-validate",
        "fixtures",
        "fixtures-validate",
        "smoke-test-state",
    ]
