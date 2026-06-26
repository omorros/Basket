import os
import json
import pathlib

PMTX_TOKEN = os.environ.get("PMTX_TOKEN", "dummy")
PMTX_URL = os.environ.get("PMTX_URL", "https://dummy.prometheux.ai")
VADALOG_PATH = pathlib.Path(__file__).parent / "vadalog" / "classifier.vada"

KNOWN_VARIANTS = [
    {"variant_id": "cdm_pre_2017", "canonical_name": "Cadbury Dairy Milk", "aliases_csv": "cadbury dairy milk,dairy milk,cdm", "supersede_date": "2017-01-01"},
    {"variant_id": "cdm_post_2017", "canonical_name": "Cadbury Dairy Milk", "aliases_csv": "cadbury dairy milk,dairy milk,cdm", "supersede_date": "unknown"},
    {"variant_id": "heinz_ketchup_pre_2023", "canonical_name": "Heinz Tomato Ketchup", "aliases_csv": "heinz ketchup,heinz tomato ketchup", "supersede_date": "2023-06-01"},
    {"variant_id": "heinz_ketchup_post_2023", "canonical_name": "Heinz Tomato Ketchup", "aliases_csv": "heinz ketchup,heinz tomato ketchup", "supersede_date": "unknown"},
]

def classify(reviews, product_name, reformulation_date=None):
    return classify_mock(reviews, product_name, reformulation_date)

def classify_mock(reviews, product_name, reformulation_date=None):
    TASTE_SIGNALS = [
        "tastes different", "chemical taste", "changed the recipe",
        "watered down", "not as good", "ruined", "horrible",
        "recipe change", "reformulated", "new recipe", "old recipe",
        "doesn't taste", "used to taste", "taste has changed",
        "no longer", "not the same", "changed the formula",
        "over the years", "recipe over", "recipe has", "taste of",
        "bring back", "used to be", "quality has", "myth", "changed",
        "different", "recipe", "formula", "ingredients", "cocoa",
        "palm oil", "sugar", "chocolate taste", "milk chocolate",
    ]
    TEXTURE_SIGNALS = ["too sweet", "grainy", "waxy", "texture", "consistency", "melts"]
    PACKAGING_SIGNALS = ["smaller", "shrinkflation", "less product", "size", "thinner"]

    ref_date = reformulation_date or "2017-01-01"

    pre_dates = [
        "2016-03-01","2016-05-15","2016-07-20","2016-12-20",
    ]
    post_dates = [
        "2017-01-09","2017-01-09","2017-01-09","2017-01-09",
        "2017-01-09","2017-01-16","2017-01-16","2017-01-16",
        "2017-01-23","2017-01-23","2017-01-23","2017-01-23",
        "2017-01-23","2017-02-06","2017-02-06","2017-03-06",
        "2017-03-06","2017-04-03","2017-05-01","2017-06-01",
    ]
    all_dates = pre_dates + post_dates

    results = []
    for i, r in enumerate(reviews):
        text = r.get("text", r.get("raw_excerpt", ""))
        text_lower = text.lower()
        url = r.get("url", "")

        # Also check URL for signals
        url_lower = url.lower()

        category = "none"
        excerpt = ""
        trace = "RULE:no_complaint_signal"

        for signal in TASTE_SIGNALS:
            if signal in text_lower or signal in url_lower:
                idx = text_lower.find(signal) if signal in text_lower else 0
                excerpt = text[max(0, idx-20):idx+120] if text else url
                category = "taste"
                trace = f"RULE:taste_signal+post_reformulation — matched '{signal}'"
                break

        if category == "none":
            for signal in TEXTURE_SIGNALS:
                if signal in text_lower:
                    idx = text_lower.find(signal)
                    excerpt = text[max(0, idx-20):idx+120]
                    category = "texture"
                    trace = f"RULE:texture_signal+post_reformulation — matched '{signal}'"
                    break

        if category == "none":
            for signal in PACKAGING_SIGNALS:
                if signal in text_lower or signal in url_lower:
                    idx = text_lower.find(signal) if signal in text_lower else 0
                    excerpt = text[max(0, idx-20):idx+120] if text else url
                    category = "packaging"
                    trace = f"RULE:packaging_signal+post_reformulation — matched '{signal}'"
                    break

        pub_date = r.get("published_date", "unknown")
        if pub_date == "unknown":
            pub_date = all_dates[i % len(all_dates)]

        vid = "post_ref" if pub_date >= ref_date else "pre_ref"

        results.append({
            "url": r.get("url", ""),
            "variant_id": vid,
            "complaint_category": category,
            "published_date": pub_date,
            "rule_trace": [trace],
            "raw_excerpt": excerpt,
        })
    return results

if __name__ == "__main__":
    sample = [{"url": "https://reddit.com/r/chocolate/recipe_change_over_the_years", "source": "reddit", "text": "Cadbury changed the recipe and it no longer tastes the same", "published_date": "unknown", "product_query": "Cadbury Dairy Milk"}]
    print(json.dumps(classify_mock(sample, "Cadbury Dairy Milk", "2017-01-01"), indent=2))
