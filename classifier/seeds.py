from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class Seeds:
    aliases: List[Tuple[str, str]]          # (alias_string, variant_id)
    supersedes: List[Tuple[str, str, str]]  # (new_variant, old_variant, reform_date_iso)
    markers: List[Tuple[str, str]]          # (phrase, category)


CATEGORY_PRECEDENCE = ["taste", "texture", "packaging", "price"]

# Placeholder demo product. Replace with the chosen product's real aliases,
# documented reformulation date, and tuned markers before the demo.
DEMO_SEEDS = Seeds(
    aliases=[
        ("coke zero", "coke-zero-2017"),
        ("coca-cola zero sugar", "coke-zero-2017"),
        ("diet coke zero", "coke-zero-2017"),
        ("coca cola zero", "coke-zero-2017"),
    ],
    supersedes=[
        ("coke-zero-2017", "coke-zero-2016", "2017-04-01"),
    ],
    markers=[
        ("tastes like chemicals", "taste"),
        ("new recipe", "taste"),
        ("changed the recipe", "taste"),
        ("doesn't taste the same", "taste"),
        ("tastes different", "taste"),
        ("watery", "texture"),
        ("flat", "texture"),
        ("new can", "packaging"),
        ("new bottle", "packaging"),
        ("price went up", "price"),
        ("too expensive", "price"),
    ],
)
