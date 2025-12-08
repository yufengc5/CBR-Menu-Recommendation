#!/usr/bin/env python3
import ast
import json
import pandas as pd
from tqdm import tqdm
import re


def remove_fraction_prefix(s):
    # Regex pattern to match fractions at the start of the string
    pattern = r'^[⅛⅓½⅔¾⅕⅖⅗⅘⅞⅐⅑⅒⅔⅕⅖⅘⅖⅞⅜⅝⅞⅝⅘⅗⅜⅞¼⅖⅗⅘⅙⅚⅛⅜⅝⅞]'
    
    # Use re.sub to replace the matched fraction with an empty string
    return re.sub(pattern, '', s).strip()


def parse_list(value):
    """Parses list-like strings from the Kaggle dataset."""
    if isinstance(value, list):
        return [remove_fraction_prefix(v) for v in value]
    if pd.isna(value):
        return []
    try:
        return [remove_fraction_prefix(v) for v in ast.literal_eval(value)]
    except:
        return []


def map_course(course_list, recipe_title):
    """Convert course_list to starter/main/dessert."""
    if not course_list:
        name = recipe_title.lower()
        if any(x in name for x in ["cake", "pie", "dessert", "cookie", "tart"]):
            return "dessert"
        return "main"

    c = [x.lower() for x in course_list]

    if any(x in c for x in ["dessert", "sweet"]):
        return "dessert"
    if any(x in c for x in ["appetizer", "starter", "side", "salad", "soup"]):
        return "starter"
    return "main"


def extract_techniques(directions_list):
    if not directions_list:
        return []

    technique_verbs = [
        "bake", "roast", "fry", "air fry", "saute", "sauté", "marinate",
        "boil", "simmer", "steam", "mix", "blend", "coat", "toss",
        "whip", "knead", "sear", "grill", "poach", "pressure cook",
        "slow cook", "broil"
    ]

    text = " ".join(directions_list).lower()
    found = [verb for verb in technique_verbs if verb in text]
    return list(set(found))


def collect_dietary_tags(row):
    tags = []

    if row.get("is_vegan", False): tags.append("vegan")
    if row.get("is_vegetarian", False): tags.append("vegetarian")
    if row.get("is_halal", False): tags.append("halal")
    if row.get("is_kosher", False): tags.append("kosher")
    if row.get("is_nut_free", False): tags.append("nut_free")
    if row.get("is_dairy_free", False): tags.append("dairy_free")
    if row.get("is_gluten_free", False): tags.append("gluten_free")

    # Also extend from dietary_profile list
    profile_list = parse_list(row.get("dietary_profile"))
    for item in profile_list:
        tags.append(str(item).lower())

    return sorted(list(set(tags)))


def build_dish_entry(row):
    return {
        "name": row["recipe_title"],
        "description": row.get("description", ""),

        "ingredients": parse_list(row["ingredients_canonical"]),
        "main_ingredient": row.get("main_ingredient", ""),

        "directions": parse_list(row["directions_raw"]),
        "techniques": extract_techniques(parse_list(row["directions_raw"])),

        "cuisines": parse_list(row["cuisine_list"]),
        "course_type": map_course(parse_list(row["course_list"]), row["recipe_title"]),

        "tastes": parse_list(row["tastes"]),
        "primary_taste": row.get("primary_taste", None),
        "secondary_taste": row.get("secondary_taste", None),

        "dietary_tags": collect_dietary_tags(row),

        "prep_time": row.get("est_prep_time_min"),
        "cook_time": row.get("est_cook_time_min"),
        "cook_speed": row.get("cook_speed", None),
        "difficulty": row.get("difficulty", "unknown"),

        "healthiness_score": row.get("healthiness_score", None),
        "health_flags": parse_list(row.get("health_flags")),
        "health_level": row.get("health_level", None),

        "popularity": {
            "fast_hits": row.get("fast_hits", 0),
            "slow_hits": row.get("slow_hits", 0),
            "medium_hits": row.get("medium_hits", 0)
        }
    }


def main():
    print("\n=== Full Dish Database Builder ===\n")

    csv_path = input("CSV filename (e.g., recipes.csv): ").strip()
    if csv_path == "":
        print("No input file.")
        return

    limit_raw = input("Limit rows? (Enter for full): ").strip()
    limit = int(limit_raw) if limit_raw.isdigit() else None

    print("\nLoading CSV…")
    df = pd.read_csv(csv_path)
    if limit:
        df = df.sample(n=limit, random_state=42)

    print(f"Loaded {len(df)} entries.\n")

    dishes = []
    print("Processing entries…")
    for _, row in tqdm(df.iterrows(), total=len(df)):
        dishes.append(build_dish_entry(row))

    out = "dish_database.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(dishes, f, indent=2, ensure_ascii=False)

    print(f"\nDONE! Saved {len(dishes)} clean dishes to {out}\n")


if __name__ == "__main__":
    main()
