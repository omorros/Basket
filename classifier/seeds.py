from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class Seeds:
    aliases: List[Tuple[str, str]]          # (alias_string, variant_id)
    supersedes: List[Tuple[str, str, str]]  # (new_variant, old_variant, reform_date_iso)
    markers: List[Tuple[str, str]]          # (phrase, category)


CATEGORY_PRECEDENCE = ["taste", "texture", "packaging", "price"]

# Locked demo product (TEAM.md, validated): Reese's Peanut Butter Cups (Hershey).
# 2026 reformulation: milk chocolate -> cheaper compound coating. Accusation breaks
# ~2026-02-17 (the reform date complaints are measured against); Hershey U-turns ~2026-04-01.
DEMO_SEEDS = Seeds(
    aliases=[
        ("reese's peanut butter cups", "reeses-compound-2026"),
        ("reeses peanut butter cups", "reeses-compound-2026"),
        ("reese's cups", "reeses-compound-2026"),
        ("reese's", "reeses-compound-2026"),
        ("reeses", "reeses-compound-2026"),
    ],
    supersedes=[
        ("reeses-compound-2026", "reeses-classic", "2026-02-17"),
    ],
    markers=[
        ("tastes different", "taste"),
        ("tastes waxy", "taste"),
        ("tastes like wax", "taste"),
        ("changed the recipe", "taste"),
        ("doesn't taste the same", "taste"),
        ("not real chocolate", "taste"),
        ("fake chocolate", "taste"),
        ("compound coating", "taste"),
        ("waxy", "texture"),
        ("greasy", "texture"),
        ("chalky", "texture"),
        ("new packaging", "packaging"),
        ("new wrapper", "packaging"),
        ("shrinkflation", "price"),
        ("price went up", "price"),
        ("too expensive", "price"),
    ],
)
