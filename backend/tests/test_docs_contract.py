from pathlib import Path


def test_api_contract_contains_required_fields() -> None:
    text = Path("../docs/api-contract.md").read_text(encoding="utf-8")
    assert "POST /api/jobs" in text
    assert "prompt_id" in text
    assert "GET /api/jobs/{job_id}/qr" in text
    assert "GET /qr/{qr_hash}" in text
