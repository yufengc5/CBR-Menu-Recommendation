#!/usr/bin/env python3
# user_query_input.py
# Visual input form to collect user preferences for the menu CBR system

import sys

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
    print("           🍽  MENU RECOMMENDER CBR")
    print("===============================================")
    print("     Please answer the following questions\n" + RESET)

def section(title):
    print("\n" + YELLOW + BOLD + f"─── {title} ───" + RESET)

def ask_text_choice(prompt, options):
    """User types the choice rather than a number."""
    print(GREEN + prompt + RESET)
    print(YELLOW + "Available options:" + RESET)
    for opt in options:
        print("  -", opt)

    while True:
        choice = input(GREEN + "Type your choice: " + RESET).strip().lower()
        for opt in options:
            if choice == opt.lower():
                return opt
        print(RED + "Invalid choice. Please type exactly one of the listed options." + RESET)

def ask_text_list(prompt, options):
    """User can type multiple values, comma-separated."""
    print(GREEN + prompt + RESET)
    print(YELLOW + "Available options (comma-separated allowed):" + RESET)
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
        print(RED + "Some entries are invalid. Please try again." + RESET)

def ask_number(prompt, minv=None, maxv=None):
    while True:
        try:
            val = int(input(GREEN + prompt + RESET))
            if (minv is None or val >= minv) and (maxv is None or val <= maxv):
                return val
        except ValueError:
            pass
        print(RED + "Invalid number. Try again." + RESET)

def ask_list(prompt):
    print(GREEN + prompt + RESET)
    raw = input(YELLOW + "Enter items separated by commas (or empty): " + RESET).strip()
    if raw == "":
        return []
    return [x.strip() for x in raw.split(",")]


# -----------------------------------------------------------
#               Main Query Builder
# -----------------------------------------------------------

def ask_query():

    banner()

    # -----------------------------
    # EVENT CONTEXT
    # -----------------------------
    section("EVENT INFORMATION")

    tipo_evento = ask_text_choice(
        "What type of event is it?",
        ["Boda", "Corporativo", "Cumpleaños", "Gala", "Congreso", "Familiar"]
    )

    estacion = ask_text_choice(
        "What season will the event take place?",
        ["Primavera", "Verano", "Otoño", "Invierno"]
    )

    pax = ask_number("How many guests will attend? ", minv=1, maxv=1000)

    # -----------------------------
    # DIETARY
    # -----------------------------
    section("DIETARY PROFILES")

    diet_groups = ask_text_list(
        "Which dietary groups must be covered?",
        ["Omnívoro", "Vegetariano", "Vegano", "Sin gluten", "Halal", "Kosher"]
    )

    forbidden = ask_list("List any forbidden ingredients:")

    # -----------------------------
    # STYLE
    # -----------------------------
    section("CULINARY STYLE")

    cuisine = ask_text_choice(
        "Preferred culinary style:",
        ["Mediterráneo", "Asiático", "Fusión", "Tradicional", "Moderno"]
    )

    techniques = ask_text_list(
        "Preferred techniques:",
        ["Asado", "Frito", "Al vapor", "Sous-vide", "A la brasa", "Marinado"]
    )

    formality = ask_text_choice(
        "Service formality:",
        ["Casual", "Semi-formal", "Formal"]
    )

    sensory = ask_text_list(
        "Desired sensory goals:",
        ["Crocante", "Cremoso", "Ácido", "Dulce", "Ahumado", "Aromático"]
    )

    print("\n" + BLUE + BOLD + "Thank you! Creating query pack..." + RESET)

    # -------------------------------------------------------
    #        RETURN MULTIPLE QUERIES (one per diet group)
    # -------------------------------------------------------
    full_queries = []

    for dg in diet_groups:
        q = {
            "Tipo_de_Evento": tipo_evento,
            "Estación_Evento": estacion,
            "Número_comensales": pax,
            "Grupo_Dietario": dg,  # SINGLE diet group per generated query
            "Ingredientes_prohibidos": forbidden,

            # Additional structured preferences
            "Culinary_Style": {
                "Cocina": cuisine,
                "Tecnicas": techniques,
                "Formalidad": formality,
                "Sensory_Goals": sensory
            }
        }
        full_queries.append(q)

    print(GREEN + BOLD + "\nGenerated Queries:" + RESET)
    for q in full_queries:
        print(YELLOW + "--------------------------------------" + RESET)
        print(q)

    return full_queries


# -----------------------------------------------------------

if __name__ == "__main__":
    queries = ask_query()
    print("\nReady to send these queries to the CBR system.")
