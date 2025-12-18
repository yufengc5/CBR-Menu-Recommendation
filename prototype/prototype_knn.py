#!/usr/bin/env python3
"""
cbr_with_dataset.py

- Loads dish_database.json (list of recipe dicts).
- Builds a TF-IDF + KNN index to retrieve top-3 similar dishes.
- Adapts retrieved dishes to user constraints (forbidden ingredients, diet).
- Produces a full CulinaryCase containing adapted menu + justifications.
"""

import json
import random
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple

# --------- Path to your dish JSON (change if necessary) ----------
DATA_PATH = "dish_database.json"   # expect a list of recipe dicts


# ----------------------------
# Reuse the case dataclasses
# (trimmed to the fields we will populate)
# ----------------------------
@dataclass
class EventLocation:
    country: str
    region: str

@dataclass
class TimeConstraints:
    prep_time: Optional[int] = None  # minutes

@dataclass
class Context:
    event_type: str
    season: str
    location: EventLocation
    number_of_guests: int
    budget_level: str
    formality_level: str
    available_ingredients: List[str]
    time_constraints: TimeConstraints

@dataclass
class FlavorPreferences:
    likes: List[str]
    dislikes: List[str]

@dataclass
class ClientProfile:
    dietary_restrictions: List[str]
    flavor_preferences: FlavorPreferences
    cultural_affinities: List[str]
    health_goals: Optional[str]
    experience_level: str

@dataclass
class SensoryGoals:
    texture: List[str]
    aromatic_profile: List[str]

@dataclass
class StyleProfile:
    chef_inspiration: List[str]
    culinary_tradition: List[str]
    techniques_emphasized: List[str]
    presentation_style: str
    sensory_goals: SensoryGoals

@dataclass
class Ingredient:
    name: str
    role: str  # "main", "secondary", "aroma", "fat", etc.

@dataclass
class Dish:
    course_type: str  # "starter"/"main"/"dessert"
    dish_name: str
    ingredients: List[Ingredient]
    techniques: List[str]
    cultural_influence: List[str]
    presentation_notes: str
    description: Optional[str] = None

@dataclass
class Menu:
    courses: List[Dish]

@dataclass
class CausalLink:
    cause: str
    effect: str

@dataclass
class Justification:
    why_this_menu: List[str]
    causal_links: List[CausalLink]
    major_adaptations: List[str]

@dataclass
class Outcome:
    client_satisfaction: float
    guest_comments: List[str]
    success_metrics: Dict[str, bool]
    adaptation_difficulties: List[str]

@dataclass
class CulinaryCase:
    id: str
    context: Context
    client_profile: ClientProfile
    style_profile: StyleProfile
    menu: Menu
    justification: Justification
    outcome: Outcome


# ----------------------------
# Utility: Load dish JSON file
# ----------------------------
def load_dish_database(path: str) -> List[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found. Put your dish_database.json next to this script or change DATA_PATH.")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("dish_database.json should contain a list of dish objects.")
    return data


# ----------------------------
# Text preprocessing helpers (simple, no parser)
# ----------------------------
def normalize_text(s: str) -> str:
    if not s:
        return ""
    return s.lower()


def ingredients_to_tokens(ingredients: List[str]) -> str:
    # ingredients likely already cleaned; join and lower
    return " ".join([normalize_text(i).replace(",", " ") for i in ingredients])


def build_document_for_recipe(recipe: dict) -> str:
    """
    Compose a textual document used for TF-IDF: title + description + ingredients + techniques + cuisines
    """
    parts = []
    parts.append(recipe.get("name", "") or recipe.get("recipe_title", ""))
    parts.append(recipe.get("description", ""))
    ings = recipe.get("ingredients", recipe.get("ingredients_raw") or [])
    if isinstance(ings, list):
        parts.append(" ".join(ings))
    else:
        parts.append(str(ings))
    parts.append(" ".join(recipe.get("techniques", [])) if recipe.get("techniques") else "")
    parts.append(" ".join(recipe.get("cuisines", recipe.get("cuisine_list") or [])))
    # include tastes and course_type as text
    parts.append(" ".join(recipe.get("tastes", []) or []))
    parts.append(str(recipe.get("course_type", recipe.get("course_list", ""))))
    return normalize_text(" ".join([p for p in parts if p]))


# ----------------------------
# Build vector index (TF-IDF + NearestNeighbors)
# ----------------------------
def build_vector_index(recipes: List[dict]):
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.neighbors import NearestNeighbors
    except ImportError as e:
        raise ImportError("scikit-learn is required for KNN retrieval. Install with `pip install scikit-learn`.") from e

    docs = [build_document_for_recipe(r) for r in recipes]
    vectorizer = TfidfVectorizer(max_features=20000, ngram_range=(1,2))
    X = vectorizer.fit_transform(docs)
    knn = NearestNeighbors(n_neighbors=10, metric="cosine", algorithm="auto")
    knn.fit(X)
    return vectorizer, knn, X


# ----------------------------
# Retrieve top-K similar recipes to a query (text)
# ----------------------------
def retrieve_knn(query_text: str, recipes: List[dict], vectorizer, knn, X, top_k=3) -> List[Tuple[int, float]]:
    """
    Returns list of (index, distance) for top_k nearest recipes.
    distances are cosine distances (lower = more similar); sklearn returns distance if metric='cosine'
    """
    q = vectorizer.transform([normalize_text(query_text)])
    dists, idxs = knn.kneighbors(q, n_neighbors=top_k, return_distance=True)
    results = []
    for dist, idx in zip(dists[0], idxs[0]):
        results.append((int(idx), float(dist)))  # index into recipes list
    return results


# ----------------------------
# Simple substitution rules (extendable)
# ----------------------------
SUBSTITUTION_RULES = {
    # animal -> plant alternatives
    "chicken": ["tofu", "seitan", "jackfruit"],
    "beef": ["seitan", "mushroom", "jackfruit"],
    "pork": ["jackfruit", "mushroom"],
    "salmon": ["tofu", "tempeh"],
    "milk": ["soy milk", "oat milk", "almond milk"],
    "butter": ["olive oil", "margarine"],
    "egg": ["flaxseed", "chia", "aquafaba"],
    "wheat": ["rice flour", "gluten-free flour"],
    "soy sauce": ["tamari"],  # tamari is typically gluten-free
    "bread": ["gluten-free bread"],
    # spices or aromatics
    "lemon": ["lime"],
    "lime": ["lemon"]
}

# Normalize keys: lower-case
SUBSTITUTION_RULES = {k.lower(): [s.lower() for s in v] for k, v in SUBSTITUTION_RULES.items()}


# ----------------------------
# Helper: check diet violation
# ----------------------------
def violates_diet(ingredient: str, diet_tags: List[str]) -> bool:
    """
    Very simple checks:
    - if diet is 'vegan' and ingredient in animal_products -> violation
    - 'vegetarian' excludes meat/fish
    This is a toy heuristic: expand via a real ontology later.
    """
    ing = ingredient.lower()
    animal = ["chicken","beef","pork","salmon","fish","shrimp","crab","lobster","egg","milk","butter","cheese","yogurt"]
    if "vegan" in diet_tags:
        return any(a in ing for a in animal)
    if "vegetarian" in diet_tags:
        # allow dairy/eggs but disallow meat/fish
        meat = ["chicken","beef","pork","salmon","fish","shrimp","crab","lobster"]
        return any(m in ing for m in meat)
    if "gluten_free" in diet_tags or "gluten-free" in diet_tags:
        # crude check: wheat, bread, flour, barley
        return any(w in ing for w in ["wheat", "bread", "flour", "barley", "semolina", "spaghetti", "pasta"])
    return False


# ----------------------------
# Adaptation engine for a single dish
# ----------------------------
def adapt_dish_ingredients(original_ingredients: List[str],
                           user_forbidden: List[str],
                           user_diets: List[str],
                           recipes_db_tokens: List[str],
                           recipes_index_map: dict) -> Tuple[List[str], List[str], List[str]]:
    """
    Attempt to adapt a dish's ingredient list given user restrictions.

    Returns:
      adapted_ingredients: list of ingredient strings
      steps: list of human-readable adaptation steps
      failures: list of ingredients that could not be adapted
    Strategy:
      - for each ingredient:
        * if ingredient contains a forbidden token -> try rule substitution
        * elif violates diet -> try rule substitution or remove
        * else keep
      - fallback: try to find a similar ingredient by looking for ingredient tokens across the dataset (recipes_db_tokens)
        (we don't use embeddings here; we use token overlap)
    """
    adapted = []
    steps = []
    failures = []

    # lower-case forbidden tokens for matching
    forbid_set = set([f.lower() for f in user_forbidden])
    diet_set = set([d.lower() for d in user_diets])

    for ing in original_ingredients:
        ing_l = ing.lower()
        replaced = False

        # quick tokenization
        tokens = [t.strip() for t in ing_l.replace("/", " ").replace("-", " ").split() if t.strip()]

        # 1) direct forbidden match (if any forbidden token in ingredient string)
        if any(f in ing_l for f in forbid_set):
            # try substitution rules
            for token in tokens:
                if token in SUBSTITUTION_RULES:
                    for candidate in SUBSTITUTION_RULES[token]:
                        if candidate not in forbid_set:
                            adapted.append(candidate)
                            steps.append(f"Replaced forbidden '{ing}' -> '{candidate}' (rule).")
                            replaced = True
                            break
                if replaced:
                    break
            if not replaced:
                # try fallback: find nearby ingredient token from recipes_db_tokens that is not forbidden and not equal
                found = None
                for cand in recipes_index_map:  # recipes_index_map is token->set(indices)
                    if cand == ing_l or cand in forbid_set:
                        continue
                    if cand in tokens:
                        continue
                    # choose first reasonable candidate
                    found = cand
                    break
                if found:
                    adapted.append(found)
                    steps.append(f"Replaced forbidden '{ing}' -> '{found}' (fallback token).")
                    replaced = True
            if not replaced:
                failures.append(ing)
                steps.append(f"Could not replace forbidden ingredient '{ing}'.")
            continue

        # 2) diet violation check (e.g., vegan)
        if violates_diet(ing_l, list(diet_set)):
            # try substitution rules per contained token
            for token in tokens:
                if token in SUBSTITUTION_RULES:
                    for candidate in SUBSTITUTION_RULES[token]:
                        # ensure candidate does not violate diet or forbidden
                        if (not violates_diet(candidate, list(diet_set))) and (candidate not in forbid_set):
                            adapted.append(candidate)
                            steps.append(f"Replaced '{ing}' -> '{candidate}' due to diet constraints.")
                            replaced = True
                            break
                if replaced:
                    break
            if not replaced:
                # If ingredient is a main protein, try to remove and replace with a plant protein placeholder
                if any(p in ing_l for p in ["chicken","beef","pork","salmon","fish"]):
                    alt = "tofu" if "vegan" in diet_set else "seitan"
                    adapted.append(alt)
                    steps.append(f"Replaced protein '{ing}' -> '{alt}' (structural adaptation).")
                    replaced = True

            if not replaced:
                failures.append(ing)
                steps.append(f"Could not adapt '{ing}' for diet {diet_set}.")
            continue

        # 3) OK to keep
        adapted.append(ing)
    return adapted, steps, failures


# ----------------------------
# Build a CulinaryCase out of recipe + adapted ingredients + justifications
# ----------------------------
def build_case_from_recipe(recipe: dict,
                           adapted_ingredients: List[str],
                           adaptation_steps: List[str],
                           adaptation_failures: List[str],
                           user_query: dict,
                           case_id: str) -> CulinaryCase:
    """
    We produce a CulinaryCase that uses:
      - context taken from user_query
      - client_profile taken from user_query
      - style from recipe (cuisine/techniques)
      - menu containing this single adapted dish
      - justification summarizing adaptation steps
    """
    # Context from user query (we expect user_query to mirror convert_case_to_simple_dict structure)
    ctx = Context(
        event_type=user_query.get("Tipo_de_Evento", "generic"),
        season=user_query.get("Estación_Evento", "any"),
        location=EventLocation(country=user_query.get("Country", "unknown"), region=user_query.get("Region", "unknown")),
        number_of_guests=user_query.get("Número_comensales", 1),
        budget_level=user_query.get("Budget", "medium"),
        formality_level=user_query.get("Formality", "casual"),
        available_ingredients=user_query.get("Available_Ingredients", []),
        time_constraints=TimeConstraints(prep_time=user_query.get("Prep_Time", None))
    )

    # client profile from query
    client = ClientProfile(
        dietary_restrictions=user_query.get("Grupo_Dietario", "").split(",") if user_query.get("Grupo_Dietario") else [],
        flavor_preferences=FlavorPreferences(likes=user_query.get("Likes", []), dislikes=user_query.get("Ingredientes_prohibidos", [])),
        cultural_affinities=user_query.get("Cultural_Affinities", []),
        health_goals=user_query.get("Health_Goals", None),
        experience_level=user_query.get("Experience_Level", "unknown")
    )

    style = StyleProfile(
        chef_inspiration=[],
        culinary_tradition=recipe.get("cuisines", []) if isinstance(recipe.get("cuisines", []), list) else recipe.get("cuisine_list", []),
        techniques_emphasized=recipe.get("techniques", []),
        presentation_style=recipe.get("presentation_notes", "") or "",
        sensory_goals=SensoryGoals(texture=recipe.get("tastes", []), aromatic_profile=[])
    )

    # build Dish object with adapted ingredients
    ingredient_objs = [Ingredient(name=a, role="main" if i == 0 else "secondary") for i, a in enumerate(adapted_ingredients)]
    dish = Dish(
        course_type=recipe.get("course_type", "main"),
        dish_name=recipe.get("name", recipe.get("recipe_title", "Unknown Recipe")),
        ingredients=ingredient_objs,
        techniques=recipe.get("techniques", []),
        cultural_influence=recipe.get("cuisines", []),
        presentation_notes=recipe.get("presentation_notes", ""),
        description=recipe.get("description", "")
    )
    menu = Menu(courses=[dish])

    # Build justification
    why = [
        f"Selected recipe '{dish.dish_name}' from dataset because it matches query preferences (similar cuisine/techniques)."
    ]
    causal_links = []
    major_adaptations = adaptation_steps.copy()
    if adaptation_failures:
        major_adaptations.append("Failed to adapt: " + ", ".join(adaptation_failures))

    justification = Justification(why_this_menu=why,
                                  causal_links=causal_links,
                                  major_adaptations=major_adaptations)

    outcome = Outcome(client_satisfaction=0.0, guest_comments=[], success_metrics={}, adaptation_difficulties=adaptation_failures)

    case = CulinaryCase(
        id=case_id,
        context=ctx,
        client_profile=client,
        style_profile=style,
        menu=menu,
        justification=justification,
        outcome=outcome
    )
    return case


# ----------------------------
# High-level pipeline: load, index, retrieve top-3, adapt, return full menu case
# ----------------------------
def generate_adapted_menu_for_query(user_query: dict, top_k: int = 3) -> CulinaryCase:
    """
    user_query should be a dict with keys similar to convert_case_to_simple_dict output,
    including at least: 'Tipo_de_Evento','Estación_Evento','Número_comensales','Grupo_Dietario',
    'Ingredientes_prohibidos', 'Culinary_Tradition', 'Techniques', 'Prep_Time', 'Available_Ingredients'.
    """
    recipes = load_dish_database(DATA_PATH)
    # Precompute recipe documents
    docs = [build_document_for_recipe(r) for r in recipes]

    # Build vector index
    vectorizer, knn, X = build_vector_index(recipes)

    # Build a textual query from user preferences: combine cuisine, techniques, ingredients, description
    q_parts = []
    q_parts.append(" ".join(user_query.get("Culinary_Tradition", [])))
    q_parts.append(" ".join(user_query.get("Techniques", [])))
    q_parts.append(" ".join(user_query.get("Available_Ingredients", [])))
    q_parts.append(" ".join(user_query.get("Sensory_Goals", [])))
    q_text = normalize_text(" ".join([p for p in q_parts if p]))

    # Retrieve top-k recipe indices
    knn_results = retrieve_knn(q_text, recipes, vectorizer, knn, X, top_k=top_k)

    # prepare a token->index map for fallback substitutions (very small heuristic)
    token_map = {}
    for idx, r in enumerate(recipes):
        # tokens from ingredients list
        ings = r.get("ingredients") or r.get("ingredients_raw") or []
        if isinstance(ings, list):
            for ing in ings:
                tok = ing.lower().strip()
                token_map.setdefault(tok, set()).add(idx)
        else:
            for tok in str(ings).lower().split(","):
                token_map.setdefault(tok.strip(), set()).add(idx)

    # From the knn results, build adapted dishes and bundle them into a multi-course menu.
    adapted_dishes = []
    all_adaptation_steps = []
    all_failures = []
    used_courses = {"starter": None, "main": None, "dessert": None}

    # iterate knn results in order, try to place them into menu slots respecting course_type
    placement_order = []
    for idx, dist in knn_results:
        placement_order.append((idx, dist))

    dish_counter = 0
    for idx, dist in placement_order:
        recipe = recipes[idx]
        # extract ingredient list (best-effort)
        raw_ings = recipe.get("ingredients") or recipe.get("ingredients_raw") or recipe.get("ingredients_canonical") or []
        if isinstance(raw_ings, list):
            ing_list = [str(x).strip() for x in raw_ings if x and str(x).strip()]
        else:
            ing_list = [t.strip() for t in str(raw_ings).split(",") if t.strip()]

        # adapt ingredients
        adapted, steps, failures = adapt_dish_ingredients(
            original_ingredients=ing_list,
            user_forbidden=user_query.get("Ingredientes_prohibidos", []),
            user_diets=user_query.get("Grupo_Dietario", "").split(",") if user_query.get("Grupo_Dietario") else [],
            recipes_db_tokens=list(token_map.keys()),
            recipes_index_map=token_map
        )

        all_adaptation_steps.extend(steps)
        all_failures.extend(failures)

        # Build adapted case/dish
        adapted_dishes.append((recipe, adapted, steps, failures))
        dish_counter += 1
        # try to fill three slots maximum
        if dish_counter >= top_k:
            break

    # Assemble menu courses: try to assign one starter, one main, one dessert in that order.
    final_courses = []
    used_slot = {"starter": False, "main": False, "dessert": False}
    slot_preference = ["starter", "main", "dessert"]

    for recipe, adapted, steps, failures in adapted_dishes:
        ctype = recipe.get("course_type") or (recipe.get("course_list")[0] if isinstance(recipe.get("course_list"), list) and recipe.get("course_list") else "main")
        ctype = ctype.lower()
        # normalize to our schema: starter/main/dessert
        if "dessert" in ctype or "sweet" in ctype:
            slot = "dessert"
        elif "appetizer" in ctype or "starter" in ctype or "entr" in ctype:
            slot = "starter"
        else:
            slot = "main"

        if not used_slot[slot]:
            # build a Dish dataclass for this adapted recipe
            dish_obj = Dish(
                course_type=slot,
                dish_name=recipe.get("name", recipe.get("recipe_title", "Unknown")),
                ingredients=[Ingredient(name=i, role="main" if j==0 else "secondary") for j,i in enumerate(adapted)],
                techniques=recipe.get("techniques", []),
                cultural_influence=recipe.get("cuisines", []),
                presentation_notes=recipe.get("presentation_notes", "") or "",
                description=recipe.get("description", "")
            )
            final_courses.append(dish_obj)
            used_slot[slot] = True

    # if some course slots empty, fill with a best-effort copy of any adapted dish
    if len(final_courses) < 3 and adapted_dishes:
        for recipe, adapted, steps, failures in adapted_dishes:
            # pick different slot if some empty
            for pref in slot_preference:
                if not used_slot[pref]:
                    dish_obj = Dish(
                        course_type=pref,
                        dish_name=recipe.get("name", recipe.get("recipe_title", "Unknown")),
                        ingredients=[Ingredient(name=i, role="main" if j==0 else "secondary") for j,i in enumerate(adapted)],
                        techniques=recipe.get("techniques", []),
                        cultural_influence=recipe.get("cuisines", []),
                        presentation_notes=recipe.get("presentation_notes", "") or "",
                        description=recipe.get("description", "")
                    )
                    final_courses.append(dish_obj)
                    used_slot[pref] = True
                    break
            if len(final_courses) >= 3:
                break

    # Build a composite CulinaryCase representing the adapted menu
    case_id = f"adapted_{random.randint(1000,9999)}"
    # pass the first recipe cuisines as style hints
    sample_recipe = recipes[knn_results[0][0]] if knn_results else {}
    adapted_case = build_case_from_recipe(
        sample_recipe,
        adapted_ingredients=[ing.name for dish in final_courses for ing in dish.ingredients],
        adaptation_steps=all_adaptation_steps,
        adaptation_failures=all_failures,
        user_query=user_query,
        case_id=case_id
    )

    # replace menu with full three-course menu
    adapted_case.menu = Menu(courses=final_courses)

    # augment justification to explain selection from KNN
    adapted_case.justification.why_this_menu.append(
        f"Retrieved top-{top_k} similar recipes from dataset using KNN over title+description+ingredients+techniques."
    )
    adapted_case.justification.causal_links.append(CausalLink(
        cause="User dietary and forbidden ingredient constraints",
        effect="Substituted/removed conflicting ingredients in the selected recipes"
    ))

    # outcome: mark adaptation difficulty if failures exist
    adapted_case.outcome.adaptation_difficulties = all_failures
    adapted_case.outcome.client_satisfaction = 0.0  # unknown until user feedback

    return adapted_case


# ----------------------------
# Simple demo: how to call generate_adapted_menu_for_query
# ----------------------------
if __name__ == "__main__":
    # Example user query (matches convert_case_to_simple_dict shape)
    user_query = {
        "Tipo_de_Evento": "wedding",
        "Estación_Evento": "winter",
        "Número_comensales": 80,
        "Grupo_Dietario": "vegan,gluten_free",   # multiple diets; pipeline checks tokens
        "Ingredientes_prohibidos": ["almond", "peanut"],   # allergies
        "Prep_Time": 30,
        "Available_Ingredients": ["potato", "olive oil", "onion"],
        "Culinary_Tradition": ["mediterranean"],
        "Techniques": ["air fry", "roast"],
        "Presentation_Style": "minimalist",
        "Sensory_Goals": ["savory","crispy"],
        "Cultural_Affinities": ["american", "mediterranean"]
    }

    print("Loading dataset and building index (this may take a few seconds)...")
    adapted_case = generate_adapted_menu_for_query(user_query, top_k=5)

    print("\n--- ADAPTED MENU CASE (JSON) ---")
    print(json.dumps(asdict(adapted_case), indent=2, ensure_ascii=False))
