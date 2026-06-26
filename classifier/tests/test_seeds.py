from classifier.seeds import DEMO_SEEDS, CATEGORY_PRECEDENCE
from classifier.contract import VALID_CATEGORIES


def test_aliases_point_to_a_known_variant():
    variants = {v for _, v in DEMO_SEEDS.aliases}
    superseding = {new for new, _, _ in DEMO_SEEDS.supersedes}
    assert variants & superseding, "at least one aliased variant must have a supersede edge"


def test_markers_use_valid_categories():
    for _, cat in DEMO_SEEDS.markers:
        assert cat in VALID_CATEGORIES


def test_precedence_covers_complaint_categories():
    assert set(CATEGORY_PRECEDENCE) == VALID_CATEGORIES - {"none"}


def test_supersedes_dates_are_iso():
    for _, _, d in DEMO_SEEDS.supersedes:
        assert len(d) == 10 and d[4] == "-" and d[7] == "-"
