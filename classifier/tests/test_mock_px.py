from classifier.px_client import MockPxClient
from classifier.seeds import DEMO_SEEDS


def _client(reviews):
    c = MockPxClient()
    c.load(reviews, DEMO_SEEDS, rules_text="")
    c.run()
    return c


def test_resolves_alias_to_variant():
    c = _client([{"url": "u1", "source": "reddit",
                  "text": "tastes waxy now", "published_date": "2026-03-12",
                  "product_query": "Reese's Peanut Butter Cups"}])
    row = c.fetch_classified()[0]
    assert row["variant_id"] == "reeses-compound-2026"


def test_post_reform_taste_classified_with_trace():
    c = _client([{"url": "u1", "source": "reddit",
                  "text": "they changed the recipe, this is not real chocolate",
                  "published_date": "2026-03-12", "product_query": "Reese's"}])
    row = c.fetch_classified()[0]
    assert row["complaint_category"] == "taste"
    assert row["raw_excerpt"]
    trace = c.trace("u1")
    assert any("post-reformulation" in t for t in trace)


def test_neutral_review_is_none():
    c = _client([{"url": "u2", "source": "reddit",
                  "text": "love these, best candy ever", "published_date": "2026-05-01",
                  "product_query": "Reese's"}])
    row = c.fetch_classified()[0]
    assert row["complaint_category"] == "none"


def test_pre_reform_complaint_not_flagged_post():
    c = _client([{"url": "u3", "source": "reddit",
                  "text": "tastes different lately", "published_date": "2025-06-01",
                  "product_query": "Reese's"}])
    trace = c.trace("u3")
    assert not any("post-reformulation" in t for t in trace)
