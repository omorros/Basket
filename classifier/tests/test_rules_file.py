from pathlib import Path

RULES = Path("classifier/rules.vada").read_text()


def test_declares_required_predicates():
    for head in ["about(", "hit(", "post_reform(", "classified("]:
        assert head in RULES, f"missing rule head {head}"


def test_marks_output_and_explanation():
    assert '@output("classified")' in RULES
    assert "@explain(" in RULES
    assert "@model(" in RULES
