#!/usr/bin/env python3
import ast
import json
import pandas as pd
import re
from tqdm import tqdm

# ======================================================
#                HELPERS
# ======================================================

def parse_list(value):
    """
    Parses fields like: "[""onion"", ""olive oil""]"
    Even though you said 'no parser', this is only for list-literals,
    not for CLI args. If this is also not allowed, I can replace it.
    """
    if isinstance(value, list):
        return value
    if pd.isna(value):
        return []
    try:
        return ast.literal_eval(value)
    except:
        return []


def map_course(course_list, recipe_title=""):
    """
    Convert dataset course tags -> starter / main / dessert.
    """
    if not course_list:
        t = recipe_title.lower()
        if any(x in t for x in ["cake", "pie", "dessert", "pudding", "cookie"]):
            return "dessert"
        return "main"

    c = [x.lower() for x in course_list]

    if any(x in c for x in ["dessert", "sweet"]):
        return "dessert"
    if any(x in c for x in ["appetizer", "starter", "side", "salad", "soup"]):
        return "starter"

    return "main"


def extract_techniques(directions_list):
    """
    Extract cooking verbs from steps.
    """
    if not directions_list:
        return []

    technique_verbs = [
        "bake","roast","fry","air fry","saute","sauté","marinate",
        "boil","simmer","steam","mix","blend","coat","toss",
        "whip","knead","sear","grill","poach","pressure cook",
        "slow cook","broil"
    ]

    text = " ".join(directions_list).lower()
    found = [verb for verb in technique_verbs if verb in text]
    return list(set(found))


# ======================================================
#           TRANSFORM A SINGLE RECIPE ROW
# ======================================================

def build_dish_entry(row):
    ingredients = parse_list(row["ingredients_canonical"])
    directions  = parse_list(row["directions_raw"])
    cuisines    = parse_list(row["cuisine_list"])
    tastes      = parse_list(row["tastes"])
    diets       = parse_list(row["dietary_profile"])
    courses     = parse_list(row["course_list"])

    return {
        "name": row["recipe_title"],
        "course_type": map_course(courses, row["recipe_title"]),
        "ingredients": ingredients,
        "techniques": extract_techniques(directions),
        "cuisines": cuisines,
        "tastes": tastes,
        "dietary_profiles": diets,
        "prep_time": int(row["est_prep_time_min"]) if pd.notna(row["est_prep_time_min"]) else None,
        "cook_time": int(row["est_cook_time_min"]) if pd.notna(row["est_cook_time_min"]) else None,
        "difficulty": row["difficulty"] if pd.notna(row["difficulty"]) else "unknown"
    }


# ======================================================
#              MAIN ENTRYPOINT (NO PARSER!)
# ======================================================

def main():
    print("\n=== Dish Database Builder ===\n")

    csv_path = input("CSV filename (e.g., recipes.csv): ").strip()
    if csv_path == "":
        print("❌ No file provided.")
        return

    limit_raw = input("Limit number of rows? (enter for full): ").strip()
    limit = int(limit_raw) if limit_raw.isdigit() else None

    print("\n📥 Loading CSV...")
    df = pd.read_csv(csv_path)

    if limit:
        df = df.head(limit)

    print(f"➡️ Loaded {len(df)} recipe records.\n")

    dishes = []
    print("🔧 Extracting data...\n")

    for _, row in tqdm(df.iterrows(), total=len(df)):
        dishes.append(build_dish_entry(row))

    output_path = "dish_database.json"
    print(f"\n💾 Saving {len(dishes)} dishes → {output_path} ...")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dishes, f, indent=2, ensure_ascii=False)

    print("\n🎉 DONE! dish_database.json is ready.\n")


if __name__ == "__main__":
    main()
