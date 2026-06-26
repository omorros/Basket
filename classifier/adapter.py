from pathlib import Path
from typing import List, Optional
from classifier.contract import validate_classified
from classifier.px_client import PxClient, MockPxClient
from classifier.seeds import Seeds, DEMO_SEEDS

_DEFAULT_RULES = str(Path(__file__).with_name("rules.vada"))


def classify(
    reviews: List[dict],
    seeds: Seeds = DEMO_SEEDS,
    client: Optional[PxClient] = None,
    rules_path: str = _DEFAULT_RULES,
) -> List[dict]:
    client = client or MockPxClient()
    rules_text = Path(rules_path).read_text() if Path(rules_path).exists() else ""
    client.load(reviews, seeds, rules_text)
    client.run()
    out = []
    for row in client.fetch_classified():
        row = dict(row)
        row["rule_trace"] = client.trace(row["url"])
        validate_classified(row)
        out.append(row)
    return out
