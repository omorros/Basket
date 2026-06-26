import json
from pathlib import Path
from classifier.run_payload import classified_payload

FIX = json.loads((Path(__file__).parents[1] / "fixtures" / "reviews.json").read_text())


def test_payload_shape():
    payload = classified_payload(FIX)
    assert set(payload) == {"reviews"}
    assert isinstance(payload["reviews"], list)
    assert payload["reviews"][0]["rule_trace"]
