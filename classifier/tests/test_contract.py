import pytest
from classifier.contract import validate_classified, VALID_CATEGORIES


def _good_row():
    return {
        "url": "https://r/1", "variant_id": "coke-zero-2017",
        "complaint_category": "taste", "published_date": "2017-05-12",
        "rule_trace": ["matched alias", "taste marker"], "raw_excerpt": "tastes weird",
    }


def test_valid_row_passes():
    validate_classified(_good_row())  # no raise


def test_missing_key_raises():
    row = _good_row(); del row["variant_id"]
    with pytest.raises(ValueError):
        validate_classified(row)


def test_bad_category_raises():
    row = _good_row(); row["complaint_category"] = "smell"
    with pytest.raises(ValueError):
        validate_classified(row)


def test_categories_are_frozen():
    assert VALID_CATEGORIES == {"taste", "texture", "packaging", "price", "none"}
