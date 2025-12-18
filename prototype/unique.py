import json
import re  # Import the Regular Expression module

def clean_ingredient_name(text):
    """
    Removes numbers, fractions, quantities, and extra spaces
    to extract the core ingredient name.
    """
    if not text:
        return ""

    # 1. Lowercase everything to ensure "Sugar" matches "sugar"
    text = text.lower()

    # 2. Remove content inside parentheses (e.g., "sugar (optional)" -> "sugar")
    text = re.sub(r'\([^)]*\)', '', text)

    # 3. Remove Unicode fractions (e.g., ⅜, ⅓, ½)
    # This range covers most common fraction characters
    text = re.sub(r'[\u00BC-\u00BE\u2150-\u215E]', '', text)

    # 4. Remove standard numbers and ASCII fractions (e.g., "1", "2.5", "1/2")
    text = re.sub(r'\d+[\d\.\/]*', '', text)

    # 5. Remove common measurement units
    # We use \b to ensure we match whole words (so "gram" doesn't delete the end of "program")
    units = [
        "cup", "cups", "tsp", "teaspoon", "tbsp", "tablespoon", 
        "oz", "ounce", "lb", "pound", "g", "gram", "kg", 
        "ml", "l", "liter", "pinch", "dash", "slice", "slices", 
        "clove", "cloves", "packet", "packets", "tightly packed"
    ]
    
    # Create a regex pattern to remove these units
    unit_pattern = r'\b(' + '|'.join(units) + r')\b'
    text = re.sub(unit_pattern, '', text)

    # 6. Remove punctuation and extra whitespace
    text = re.sub(r'[,\.\-]', ' ', text) # Replace punctuation with space
    text = " ".join(text.split()) # clear double spaces
    
    return text

def extract_unique_values(data):
    unique_data = {
        "ingredients": set(),
        "flavors": set(),
        "cultural_affinities": set(),
        "techniques": set(),
        "textures": set()
    }
    
    if isinstance(data, dict): data = [data]

    for recipe in data:
        # --- CLEANING INGREDIENTS HERE ---
        if recipe.get("ingredients"):
            for ing in recipe["ingredients"]:
                # Run the cleaner on every ingredient
                clean_name = clean_ingredient_name(ing)
                if clean_name: # Only add if not empty
                    unique_data["ingredients"].add(clean_name)

        # Techniques
        if recipe.get("techniques"): unique_data["techniques"].update(recipe["techniques"])
        # Cuisines
        if recipe.get("cuisines"): unique_data["cultural_affinities"].update(recipe["cuisines"])
        # Flavors
        if recipe.get("tastes"): unique_data["flavors"].update(recipe["tastes"])
        if recipe.get("primary_taste") and recipe["primary_taste"] != "unknown": unique_data["flavors"].add(recipe["primary_taste"])
        if recipe.get("secondary_taste") and recipe["secondary_taste"] != "unknown": unique_data["flavors"].add(recipe["secondary_taste"])
        # Textures
        if recipe.get("texture"):
             val = recipe["texture"]
             if isinstance(val, list): unique_data["textures"].update(val)
             else: unique_data["textures"].add(val)

    return {k: sorted(list(v)) for k, v in unique_data.items()}

if __name__ == "__main__":
    try:
        # Replace with your actual filename
        with open('dish_database.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        results = extract_unique_values(data)
        
        print(f"Ingredients: {', '.join(results['ingredients'])}")
        print("-" * 20)
        print(f"Flavors: {', '.join(results['flavors'])}")
        print("-" * 20)
        print(f"Techniques: {', '.join(results['techniques'])}")
        print("-" * 20)
        print(f"Cultural Affinities: {', '.join(results['cultural_affinities'])}")
        print("-" * 20)
        print(f"Textures: {', '.join(results['textures'])}")

    except FileNotFoundError:
        print("Error: recipes.json file not found.")