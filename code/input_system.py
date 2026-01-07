import sys

# ---------- COLORS ----------
BLUE   = "\033[94m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


# prints the name of the program
def banner():
    print(BLUE + BOLD)
    print("===============================================================")
    print("                     THE GRAND CHEF")
    print("===============================================================")
    print(" Get menu recommendation for all types of events and clients.\n" + RESET)

# prints section title
def section(title):
    print("\n" + YELLOW + BOLD + f"─── {title} ───" + RESET)

# Asks a single-choice text question
def ask_text_choice(prompt, options, required=True):
    """Single choice (like <select required>)."""
    print(GREEN + prompt + RESET)
    print(YELLOW + "Options:" + RESET)
    for opt in options:
        print("  -", opt)

    if not required:
        print(YELLOW + "(Press Enter to skip)" + RESET)

    # Must match exactly one option
    while True:
        choice = input(GREEN + "Your choice: " + RESET).strip()
        if choice == "" and not required:
            return None
        choice_l = choice.lower()
        for opt in options:
            if choice_l == opt.lower():
                return opt
        print(RED + "Invalid. Type exactly one option." + RESET)

# Asks a multi-choice text question
def ask_text_list(prompt, options, required=False):
    """Multi-select (like <select multiple>). Empty allowed unless required=True."""
    print(GREEN + prompt + RESET)
    print(YELLOW + "Options (comma-separated allowed):" + RESET)
    for opt in options:
        print("  -", opt)

    if not required:
        print(YELLOW + "(Press Enter for none)" + RESET)

    while True:
        raw = input(GREEN + "Your selections: " + RESET).strip()
        if raw == "":
            if required:
                print(RED + "At least one selection required." + RESET)
                continue
            return []
        
        parts = [p.strip().lower() for p in raw.split(",") if p.strip() != ""]
        valid = []
        for p in parts:
            matched = False
            for opt in options:
                if p == opt.lower():
                    valid.append(opt)
                    matched = True
                    break
            if not matched:
                valid = None
                break

        # Ensure all valid selections
        if valid is not None and len(valid) == len(parts):
            dedup = []
            seen = set()
            for v in valid:
                if v.lower() not in seen:
                    dedup.append(v)
                    seen.add(v.lower())
            return dedup

        print(RED + "Some entries invalid. Try again." + RESET)

# Asks a numeric input
def ask_number(prompt, minv=None, maxv=None, required=True):
    while True:
        raw = input(GREEN + prompt + RESET).strip()
        if raw == "" and not required:
            return None
        try:
            v = int(raw)
            if (minv is None or v >= minv) and (maxv is None or v <= maxv):
                return v
        except:
            pass
        print(RED + "Invalid number." + RESET)

def ask_text(prompt, required=True, placeholder=None):
    """Plain Text input"""
    if placeholder:
        print(YELLOW + f"Example: {placeholder}" + RESET)
    while True:
        val = input(GREEN + prompt + RESET).strip()
        if val == "":
            if required:
                print(RED + "This field is required." + RESET)
                continue
            return ""
        return val

def ask_comma_separated_text(prompt, required=False, placeholder=None):
    """Multi-value text input from comma-separated."""
    if placeholder:
        print(YELLOW + f"Example: {placeholder}" + RESET)
    while True:
        raw = input(GREEN + prompt + RESET).strip()
        if raw == "":
            if required:
                print(RED + "This field is required." + RESET)
                continue
            return []
        return [x.strip() for x in raw.split(",") if x.strip()]


# Main function to ask for query input
def ask_query(saved=False):
    banner()

    if saved:
        print(GREEN + BOLD + "You have successfully saved your information!" + RESET)

    # Event info
    section("Event Information")

    event_type = ask_text_choice(
        "Event type",
        ["casual_dinner", "wedding", "business_lunch", "birthday", "formal_gala", "party"],
        required=True)

    season = ask_text_choice(
        "Season",
        ["spring", "summer", "autumm", "winter"],
        required=True)

    number_of_guests = ask_number(
        "Number of guests: ",
        minv=1,
        required=True)

    description = ask_text(
        "Description of the event: ",
        required=True,
        placeholder="e.g. A dinner with my coworkers.")

    # Dietary Restrictions
    section("Dietary Restrictions")

    dietary = ask_text_choice(
    "Dietary Restriction (choose one):",
    ["none", "vegan", "vegetarian", "halal", "gluten_free", "lactose_free", "kosher"],
    required=True)

    # Preferences
    section("Preferences")

    print(YELLOW + "Hold Ctrl (Cmd on Mac) to select multiple. (CLI: type comma-separated)\n" + RESET)
    preferred_techniques = ask_text_list(
        "Preferred techniques (multiple allowed)",
        ["air_fry", "bake", "blend", "boil", "broil", "coat", "fry", "grill", "knead",
         "marinate", "mix", "poach", "pressure_cook", "roast", "saute", "sear", "simmer",
         "slow_cook", "steam", "toss", "whip"],
        required=False)

    presentation_style = ask_text_choice(
        "Presentation Style",
        ["buffet", "plated", "casual"],
        required=True)

    sensory_goals = ask_text_list(
        "Sensory Goals (multiple allowed)",
        ["sweet", "spicy", "sour", "savory", "salty", "comforting", "bitter", "umami",
         "smoky", "earthy", "crispy", "creamy", "exotic", "refreshing"],
        required=False)

    culinary_traditions = ask_text_list(
        "Culinary Traditions (multiple allowed)",
        ["molecular_gastronomy", "author_cuisine_arzak", "classic_french", "nordic", "african", "american", "american_region", "asian", "british", "caribbean", "chinese",
         "european", "filipino", "french", "german", "greek", "indian", "italian", "japanese",
         "korean", "latin_american", "mediterranean", "mexican", "middle_eastern",
         "middle_eastern_region", "russian", "spanish", "thai", "turkish", "unknown", "vietnamese"],
        required=False)

    forbidden_ingredients = ask_comma_separated_text(
        "Forbidden Ingredients: ",
        required=False,
        placeholder="e.g. potato,tomato (comma-separated)")

    prep_time = ask_number(
        "Preparation Time: ",
        minv=1,
        required=True)

    healthiness_level = ask_text_choice(
        "Healthiness Level",
        ["healthy", "moderate", "unhealthy"],
        required=True)

    # final result
    result = {
        "event_type": event_type,
        "season": season,
        "number_of_guests": number_of_guests,
        "description": description,
        "dietary_group": dietary,
        "preferred_techniques": preferred_techniques,
        "presentation_style": presentation_style,
        "sensory_goals": sensory_goals,
        "culinary_traditions": culinary_traditions,
        "forbidden_ingredients": forbidden_ingredients,
        "prep_time": prep_time,
        "healthiness_level": healthiness_level,
    }
    return result

# Main function to ask for response input
def ask_response():
    print(GREEN + BOLD + "\nPlease provide your feedback on the recommended menu." + RESET)

    rating = ask_number(
        "Rating (1-5): ",
        minv=1,
        maxv=5,
        required=True)

    feedback = ask_text(
        "Additional comments (optional): ",
        required=False)

    return {
        "rating": rating,
        "feedback": feedback}


# Test function
if __name__ == "__main__":
    data = ask_query(saved=False)
    response = ask_response()
