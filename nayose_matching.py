
import pandas as pd
from difflib import SequenceMatcher
from pathlib import Path

# Load both datasets
source = pd.read_csv("synthetic_customers.csv", dtype=str).fillna("")
target = pd.read_csv("insurance_test_data.csv", dtype=str).fillna("")


def normalize(value):
    """Normalize text for comparison."""
    return "".join(str(value).casefold().split())


def similarity(value1, value2):
    """Return similarity percentage between two values."""
    a = normalize(value1)
    b = normalize(value2)

    if not a or not b:
        return 0.0

    return round(SequenceMatcher(None, a, b).ratio() * 100, 2)


results = []

# Compare every source customer with every target customer
for _, src in source.iterrows():
    for _, tgt in target.iterrows():

        kanji_score = similarity(
            src["customer_name"], tgt["customer_name"]
        )
        kana_score = similarity(
            src["name_kana"], tgt["name_kana"]
        )
        romaji_score = similarity(
            src["name_romaji"], tgt["name_romaji"]
        )
        address_score = similarity(
            src["address"], tgt["address"]
        )
        phone_score = similarity(
            src["phone"], tgt["phone"]
        )

        # Combine the three name formats into one name score
        name_score = round(
            kanji_score * 0.50
            + kana_score * 0.30
            + romaji_score * 0.20,
            2
        )

        # Overall score: name 60%, address 25%, phone 15%
        overall_score = round(
            name_score * 0.60
            + address_score * 0.25
            + phone_score * 0.15,
            2
        )

        same_name = (
            normalize(src["customer_name"])
            == normalize(tgt["customer_name"])
        )
        same_address = (
            normalize(src["address"])
            == normalize(tgt["address"])
        )
        same_phone = (
            normalize(src["phone"])
            == normalize(tgt["phone"])
        )

        if same_name and same_address and same_phone:
            category = "Exact Match"
        elif (
            name_score >= 90
            and address_score >= 90
            and phone_score >= 90
        ):
            category = "Strong Candidate"
        elif (
            (name_score >= 80 and address_score >= 80)
            or overall_score >= 70
        ):
            category = "Review Required"
        else:
            category = "Non-Match"

        results.append({
            "source_customer_id": src["customer_id"],
            "source_name_kanji": src["customer_name"],
            "source_name_kana": src["name_kana"],
            "source_name_romaji": src["name_romaji"],
            "target_customer_id": tgt["customer_id"],
            "target_name_kanji": tgt["customer_name"],
            "target_name_kana": tgt["name_kana"],
            "target_name_romaji": tgt["name_romaji"],
            "kanji_score": kanji_score,
            "kana_score": kana_score,
            "romaji_score": romaji_score,
            "name_score": name_score,
            "address_score": address_score,
            "phone_score": phone_score,
            "overall_score": overall_score,
            "match_category": category,
        })


# Create report
report = pd.DataFrame(results)
report = report.sort_values(
    ["source_customer_id", "overall_score"],
    ascending=[True, False]
)

report.to_csv(
    "nayose_matching_report.csv",
    index=False,
    encoding="utf-8-sig"
)

# Create manual review report
review = report[
    report["match_category"] == "Review Required"
]
review.to_csv(
    "nayose_review.csv",
    index=False,
    encoding="utf-8-sig"
)

# Create summary report
summary = (
    report["match_category"]
    .value_counts()
    .rename_axis("match_category")
    .reset_index(name="pair_count")
)
summary["percentage"] = (
    summary["pair_count"] / len(report) * 100
).round(2)

summary.to_csv(
    "nayose_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Nayose matching completed!")
print(f"Source records: {len(source)}")
print(f"Target records: {len(target)}")
print(f"Pairs compared: {len(report)}")
print("\nMatch category summary:")
print(summary.to_string(index=False))
print("\nTop 10 candidate pairs:")
print(
    report[
        [
            "source_customer_id",
            "target_customer_id",
            "name_score",
            "address_score",
            "phone_score",
            "overall_score",
            "match_category",
        ]
    ].head(10).to_string(index=False)
)
print("\nReports saved:")
print("- nayose_matching_report.csv")
print("- nayose_review.csv")
print("- nayose_summary.csv")
