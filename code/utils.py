'''
Utility script to generate datasets out of the dishes data.
'''

import json
import csv

# Load the JSON file containing multiple recipes
with open("data/dish_database_5k.json", "r", errors="ignore", encoding="utf-8") as f:
    recipes = json.load(f)  # assuming it's a list of recipe objects

# Collect all ingredients from all recipes
all_ingredients = []
for recipe in recipes:
    all_ingredients.extend(recipe.get("techniques", []))

# Remove duplicates and sort alphabetically
unique_ingredients = sorted(set(all_ingredients))

# Save as CSV
with open("data/techniques.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    for ingredient in unique_ingredients:
        writer.writerow([ingredient])

print(f"Saved {len(unique_ingredients)} unique cuisines to CSV file.")
