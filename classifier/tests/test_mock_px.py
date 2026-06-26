from classifier.px_client import MockPxClient
from classifier.seeds import DEMO_SEEDS


def _client(reviews):
    c = MockPxClient()
    c.load(reviews, DEMO_SEEDS, rules_text="")
    c.run()
    return c


def test_resolves_alias_to_variant():
    c = _client([{"url": "u1", "source": "reddit",
                  "text": "tastes like chemicals now", "published_date": "2017-05-12",
                  "product_query": "Coke Zero"}])
    row = c.fetch_classified()[0]
    assert row["variant_id"] == "coke-zero-2017"


def test_post_reform_taste_classified_with_trace():
    c = _client([{"url": "u1", "source": "reddit",
                  "text": "this tastes like chemicals now", "published_date": "2017-05-12",
                  "product_query": "Coca-Cola Zero Sugar"}])
    row = c.fetch_classified()[0]
    assert row["complaint_category"] == "taste"
    assert row["raw_excerpt"]
    trace = c.trace("u1")
    assert any("post-reformulation" in t for t in trace)


def test_neutral_review_is_none():
    c = _client([{"url": "u2", "source": "reddit",
                  "text": "love this drink, perfect", "published_date": "2018-01-01",
                  "product_query": "Coke Zero"}])
    row = c.fetch_classified()[0]
    assert row["complaint_category"] == "none"


def test_pre_reform_complaint_not_flagged_post():
    c = _client([{"url": "u3", "source": "reddit",
                  "text": "tastes different lately", "published_date": "2016-01-01",
                  "product_query": "Coke Zero"}])
    trace = c.trace("u3")
    assert not any("post-reformulation" in t for t in trace)
