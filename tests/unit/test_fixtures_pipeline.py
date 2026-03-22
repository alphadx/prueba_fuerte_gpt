import json
import subprocess
from pathlib import Path


def test_fixtures_pipeline_generates_critical_catalog(tmp_path: Path) -> None:
    report_path = tmp_path / "fixtures.json"

    run_loader = subprocess.run(
        ["python3", "infra/scripts/load_fixtures.py", "--output", str(report_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run_loader.returncode == 0, run_loader.stderr
    assert report_path.exists()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    required = {
        "FX-SALE-CASH",
        "FX-SALE-ELECTRONIC",
        "FX-WEB-PICKUP",
        "FX-BILLING-SBX",
        "FX-PAYMENT-WEBHOOK",
    }
    assert required.issubset(set(payload.get("fixtures", {}).keys()))

    run_validate = subprocess.run(
        ["python3", "infra/scripts/validate_fixtures.py", "--path", str(report_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run_validate.returncode == 0, run_validate.stderr
    assert "[fixtures] OK: catálogo crítico completo" in run_validate.stdout
