#!/usr/bin/env python3
# user_query_input_v2.py
# COMPLETE visual input form for the new CulinaryCase-based menu CBR system

import sys

# ---------- COLORS ----------
BLUE   = "\033[94m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


# -----------------------------------------------------------
#                 Visual Helpers
# -----------------------------------------------------------

def banner():
    print(BLUE + BOLD)
    print("===============================================")
    print("          🍽  ADVANCED MENU CBR INPUT")
    print("===============================================")
    print("      Provide event + client + style details\n" + RESET)

def section(title):
    print("\n" + YELLOW + BOLD + f"─── {title} ───" + RESET)

def ask_text_choice(prompt, options):
    print(GREEN + prompt + RESET)
    print(YELLOW + "Options:" + RESET)
    for opt in options:
        print("  -", opt)

    while True:
        choice = input(GREEN + "Your choice: " + RESET).strip().lower()
        for opt in options:
            if choice == opt.lower():
                return opt
        print(RED + "Invalid. Type exactly one option." + RESET)

def ask_text_list(prompt, options):
    print(GREEN + prompt + RESET)
    print(YELLOW + "Options (comma-separated allowed):" + RESET)
    for opt in options:
        print("  -", opt)

    while True:
        raw = input(GREEN + "Your selections: " + RESET).strip()
        if raw == "":
            return []
        parts = [p.strip().lower() for p in raw.split(",")]
        valid = []
        for p in parts:
            for opt in options:
                if p == opt.lower():
                    valid.append(opt)
                    break
        if len(valid) == len(parts):
            return valid
        print(RED + "Some entries invalid. Try again." + RESET)

def ask_number(prompt, minv=None, maxv=None):
    while True:
        try:
            v = int(input(GREEN + prompt + RESET))
            if (minv is None or v >= minv) and (maxv is None or v <= maxv):
                return v
        except:
            pass
        print(RED + "Invalid number." + RESET)

def ask_list(prompt):
    print(GREEN + prompt + RESET)
    raw = input(YELLOW + "Comma-separated (or empty): " + RESET).strip()
    if raw == "":
        return []
    return [x.strip() for x in raw.split(",")]


# ===========================================================
#                   ASK NEW FULL QUERY
# ===========================================================

def ask_query():

    banner()

    # -------------------------------------------------------
    # EVENT CONTEXT
    # -------------------------------------------------------
    section("EVENT CONTEXT")

    event_type = ask_text_choice(
        "Type of event:",
        ["wedding", "gala", "family_event", "congress", "corporate"]
    )

    season = ask_text_choice(
        "Season of the event:",
        ["spring", "summer", "autumn", "winter"]
    )

    number_of_guests = ask_number(
        "Number of guests (>0): ",
        minv=1, maxv=2000
    )

    budget = ask_text_choice(
        "Budget level:",
        ["low", "medium", "high", "premium"]
    )

    formality = ask_text_choice(
        "Service formality:",
        ["casual", "semi-formal", "formal"]
    )

    prep_time = ask_text_choice(
        "Allowed preparation time:",
        ["short", "medium", "long"]
    )

    # -------------------------------------------------------
    # CLIENT PROFILE
    # -------------------------------------------------------
    section("CLIENT PROFILE")

    diet_groups = ask_text_list(
        "Dietary restriction groups (multiple allowed):",
        ["omnivore", "vegetarian", "vegan", "gluten-free", "halal", "kosher"]
    )

    forbidden_ingredients = ask_list(
        "Forbidden ingredients for this group:"
    )

    flavor_likes = ask_list("Flavors they LIKE:")
    flavor_dislikes = ask_list("Flavors they DISLIKE:")

    cultural_affinities = ask_list(
        "Cultural affinities (e.g. Mediterranean, Japanese, Italian):"
    )

    health_goals = ask_text_choice(
        "Health goal:",
        ["light", "high-protein", "low-salt", "none"]
    )

    experience_level = ask_text_choice(
        "Experience level (how bold the menu can be):",
        ["traditional", "adventurous", "experimental"]
    )

    # -------------------------------------------------------
    # CULINARY STYLE & SENSORY GOALS
    # -------------------------------------------------------
    section("CULINARY STYLE")

    culinary_tradition = ask_list(
        "Preferred culinary traditions (Mediterranean, Nordic, etc.):"
    )

    techniques_emphasized = ask_list(
        "Preferred techniques (fermentation, sous-vide, etc.):"
    )

    presentation_style = ask_text_choice(
        "Presentation style:",
        ["rustic", "minimalist", "elegant", "artistic", "simple"]
    )

    sensory_texture = ask_list(
        "Desired TEXTURES (creamy, crunchy, silky, etc.):"
    )

    sensory_aroma = ask_list(
        "Desired AROMATIC notes (herbal, citrus, smoky, etc.):"
    )

    # -------------------------------------------------------
    #   BUILD ONE QUERY PER DIETARY GROUP
    # -------------------------------------------------------
    section("BUILDING QUERY PACK")

    full_queries = []

    for dg in diet_groups:

        q = {
            # CBR-compatible Problem fields
            "Tipo_de_Evento": event_type,
            "Estación_Evento": season,
            "Número_comensales": number_of_guests,
            "Grupo_Dietario": dg,
            "Ingredientes_prohibidos": forbidden_ingredients,

            # EXTENDED similarity fields:
            "Prep_Time": prep_time,
            "Culinary_Tradition": [c.lower() for c in culinary_tradition],
            "Techniques": [t.lower() for t in techniques_emphasized],
            "Presentation_Style": presentation_style,
            "Sensory_Goals": [*sensory_texture, *sensory_aroma],
            "Cultural_Affinities": cultural_affinities,
        }

        full_queries.append(q)

    # -------------------------------------------------------
    # PRINT RESULTING QUERY PACK
    # -------------------------------------------------------
    print(GREEN + BOLD + "\nGENERATED QUERIES:" + RESET)
    for q in full_queries:
        print(YELLOW + "--------------------------------------" + RESET)
        print(q)

    return full_queries


# ============================================================

if __name__ == "__main__":
    queries = ask_query()
    print("\nReady to send these queries to the CBR system.")
