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
        # Reese's (validated demo product)
        ("reese's peanut butter cups", "reeses-compound-2026"),
        ("reeses peanut butter cups", "reeses-compound-2026"),
        ("reese's cups", "reeses-compound-2026"),
        ("reese's", "reeses-compound-2026"),
        ("reeses", "reeses-compound-2026"),
        # Additional demo products (entity resolution so variant != unknown)
        ("cadbury dairy milk", "cadbury-recipe"),
        ("dairy milk", "cadbury-recipe"),
        ("cadbury", "cadbury-recipe"),
        ("m&m's", "mms-dye-2026"),
        ("m&ms", "mms-dye-2026"),
        ("m and m's", "mms-dye-2026"),
        ("walkers crisps", "walkers-salt-2025"),
        ("walkers", "walkers-salt-2025"),
        ("doritos", "doritos-recipe"),
        ("toblerone", "toblerone-2016"),
        ("quality street", "qualitystreet-2022"),
        ("heinz tomato ketchup", "heinz-2023"),
        ("heinz ketchup", "heinz-2023"),
    ],
    supersedes=[
        # (new_variant, old_variant, default_date) — the orchestrator overrides the
        # date per run with the reformulation date it resolves for that product.
        ("reeses-compound-2026", "reeses-classic", "2026-02-17"),
        ("cadbury-recipe", "cadbury-classic", "2024-01-01"),
        ("mms-dye-2026", "mms-classic", "2026-06-19"),
        ("walkers-salt-2025", "walkers-classic", "2025-08-12"),
        ("doritos-recipe", "doritos-classic", "2025-01-01"),
        ("toblerone-2016", "toblerone-classic", "2016-11-08"),
        ("qualitystreet-2022", "qualitystreet-classic", "2022-10-03"),
        ("heinz-2023", "heinz-classic", "2023-06-01"),
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
        ("watered down", "taste"),
        ("ruined", "taste"),
        ("not the same", "taste"),
        ("bring back the old", "taste"),
        ("less salty", "taste"),
        ("reformulat", "taste"),
        ("waxy", "texture"),
        ("greasy", "texture"),
        ("chalky", "texture"),
        ("gritty", "texture"),
        ("new packaging", "packaging"),
        ("new wrapper", "packaging"),
        ("paper wrapper", "packaging"),
        ("smaller", "packaging"),
        ("shrinkflation", "price"),
        ("price went up", "price"),
        ("too expensive", "price"),
    ],
)
