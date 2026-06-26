import json
from pathlib import Path
from classifier.adapter import classify
from classifier.contract import validate_classified

FIX = json.loads((Path(__file__).parents[1] / "fixtures" / "reviews.json").read_text())


def test_output_is_contract_valid():
    out = classify(FIX)
    assert len(out) == len(FIX)
    for row in out:
        validate_classified(row)
        assert row["rule_trace"], "rule_trace must be populated"


def test_known_post_reform_taste_row():
    out = {r["url"]: r for r in classify(FIX)}
    row = out["https://reddit.com/r/post1"]
    assert row["variant_id"] == "reeses-compound-2026"
    assert row["complaint_category"] == "taste"
    assert any("post-reformulation" in t for t in row["rule_trace"])


def test_neutral_row_is_none():
    out = {r["url"]: r for r in classify(FIX)}
    assert out["https://reddit.com/r/neutral1"]["complaint_category"] == "none"
