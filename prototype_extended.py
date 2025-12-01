import json
import random
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

# ============================================================
# Dataclass case representation (same as we discussed)
# ============================================================

@dataclass
class EventLocation:
    country: str
    region: str
    urban_or_rural: str  # "urban" / "rural"

@dataclass
class TimeConstraints:
    prep_time: str  # "short", "medium", "long"
    serving_duration: str  # "buffet", "timed_service"

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
    temperature_contrast: bool
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
    role: str  # e.g., "main", "secondary", "aroma", "fat"

@dataclass
class Dish:
    course_type: str  # starter/main/dessert...
    dish_name: str
    ingredients: List[Ingredient]
    techniques: List[str]
    cultural_influence: List[str]
    presentation_notes: str

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

# Convenience example case (same contents as before)
def example_case(case_id="case_001") -> CulinaryCase:
    return CulinaryCase(
        id=case_id,
        context=Context(
            event_type="Boda",  # Spanish labels to match prototype style
            season="Invierno",
            location=EventLocation(country="España", region="Cataluña", urban_or_rural="urbano"),
            number_of_guests=120,
            budget_level="alto",
            formality_level="formal",
            available_ingredients=["alcachofa", "limón", "lubina", "almendras"],
            time_constraints=TimeConstraints(prep_time="largo", serving_duration="timed_service")
        ),
        client_profile=ClientProfile(
            dietary_restrictions=["Sin gluten"],  # note Spanish phrasing to align
            flavor_preferences=FlavorPreferences(likes=["cítrico", "umami"], dislikes=["amargo"]),
            cultural_affinities=["Mediterránea", "Japonesa"],
            health_goals="ligero",
            experience_level="adventurero"
        ),
        style_profile=StyleProfile(
            chef_inspiration=["Ferran Adrià", "Noma"],
            culinary_tradition=["Catalana", "Nórdica"],
            techniques_emphasized=["fermentación", "espumas", "sous-vide"],
            presentation_style="minimalista",
            sensory_goals=SensoryGoals(texture=["cremoso", "crujiente"], temperature_contrast=True, aromatic_profile=["herbal", "cítrico"])
        ),
        menu=Menu(courses=[
            Dish(course_type="starter", dish_name="Texturas de alcachofa con espuma cítrica",
                 ingredients=[Ingredient("alcachofa", "principal"), Ingredient("limón", "aroma"), Ingredient("aceite de oliva", "grasa")],
                 techniques=["asado", "emulsión", "espuma molecular"], cultural_influence=["Mediterránea"], presentation_notes="emplatado vertical con espuma arriba"),
            Dish(course_type="main", dish_name="Lubina glaseada con cebada fermentada",
                 ingredients=[Ingredient("lubina", "principal"), Ingredient("miso", "condimento"), Ingredient("cebada", "base")],
                 techniques=["glaseado", "fermentación", "cocción lenta"], cultural_influence=["Japonesa"], presentation_notes="emplatado minimalista")
        ]),
        justification=Justification(
            why_this_menu=["Uso de ingredientes de temporada: alcachofa, cítricos", "Alineado con preferencias mediterráneo/japonés", "Emplatado formal minimalista", "Se sustituyó soja por tamari sin gluten"],
            causal_links=[CausalLink("estación invierno", "platos calientes y reconfortantes"), CausalLink("perfil aventurero", "uso de técnicas moleculares")],
            major_adaptations=["Tamari en vez de salsa de soja", "Blanquear alcachofas para reducir amargor"]
        ),
        outcome=Outcome(
            client_satisfaction=4.7,
            guest_comments=["Postre memorable", "Excelente equilibrio cítrico"],
            success_metrics={"budget_compliance": True, "ingredient_availability": True, "timeliness": True},
            adaptation_difficulties=["Sustitución de almendras por alergia"]
        )
    )

# ============================================================
# Conversion utilities: dataclass case -> simple dict case
# (Target format matches the prototype: Spanish keys used in prototype)
# ============================================================

def convert_case_to_simple_dict(case: CulinaryCase) -> dict:
    """
    Convert a CulinaryCase (dataclass) into the simple dictionary format
    used by the existing prototype (Spanish key names).
    """
    d = asdict(case)

    # Map course types from English-like keys we used to Spanish menu slots
    course_map = {
        "starter": "Primero",
        "main": "Segundo",
        "dessert": "Postre",
        # provide fallback mapping if other types appear
        "side": "Primero",
        "drink": "Postre"
    }

    # Problem (query-like) fields (keeping Spanish names)
    problem = {
        "Tipo_de_Evento": d["context"]["event_type"],
        "Estación_Evento": d["context"]["season"],
        "Número_comensales": d["context"]["number_of_guests"],
        # Use a conservative mapping for Grupo_Dietario:
        # If client_profile.dietary_restrictions contains explicit diets like "Vegetariano",
        # try to provide that; otherwise fall back to experience_level.
        "Grupo_Dietario": infer_diet_group(d["client_profile"]),
        "Ingredientes_prohibidos": d["client_profile"]["dietary_restrictions"] or []
    }

    # Solution: build Platos mapping with Spanish keys
    platos = {}
    for dish in d["menu"]["courses"]:
        ctype = dish["course_type"]
        spanish_course = course_map.get(ctype, None)
        if spanish_course:
            platos[spanish_course] = {"Nombre": dish["dish_name"]}
    # Ensure keys exist to avoid KeyError in Reuser
    for key in ("Primero", "Segundo", "Postre"):
        if key not in platos:
            platos[key] = {"Nombre": ""}

    simple_case = {
        "id": d["id"],
        "problem": problem,
        "solution": {"Platos": platos}
    }
    return simple_case

def infer_diet_group(client_profile_dict: dict) -> str:
    """
    Infer a Grupo_Dietario from the client's dietary_restrictions if possible.
    Fallback order: explicit keywords -> experience_level.
    """
    restrictions = [r.lower() for r in (client_profile_dict.get("dietary_restrictions") or [])]
    if any("veget" in r for r in restrictions):
        return "Vegetariano"
    if any("vegano" in r or "veg" == r for r in restrictions):
        return "Vegano"
    if any("sin gluten" in r or "celíaco" in r for r in restrictions):
        return "Sin gluten"
    # fallback to experience_level (which in example contains "adventurero")
    exp = client_profile_dict.get("experience_level", "")
    if exp:
        # map some known words to our Grupo_Dietario space
        if "advent" in exp or "experiment" in exp or "adventur" in exp:
            return "Omnívoro"  # default broad group
    return "Omnívoro"

# ============================================================
# Your original prototype classes (Retriever, Reuser, Reviser, Retainer)
# Slightly adjusted to handle the possibility that some "Nombre" are empty strings
# ============================================================

class Retriever:
    def __init__(self, case_base):
        self.case_base = case_base

        # Weight configuration
        self.weights = {
            "Tipo": 0.30,
            "Estacion": 0.20,
            "Diet": 0.30,
            "Pax": 0.10,
            "Forbidden": 0.10
        }

    def similarity(self, case1, case2):
        # case1 and case2 are simple dicts with Spanish keys as in the prototype
        score = 0.0
        w = self.weights

        if case1.get("Tipo_de_Evento") == case2.get("Tipo_de_Evento"):
            score += w["Tipo"]
        if case1.get("Estación_Evento") == case2.get("Estación_Evento"):
            score += w["Estacion"]
        if case1.get("Grupo_Dietario") == case2.get("Grupo_Dietario"):
            score += w["Diet"]

        diff = abs(int(case1.get("Número_comensales", 0)) - int(case2.get("Número_comensales", 0)))
        pax_sim = max(0, 1 - diff / 500)
        score += pax_sim * w["Pax"]

        s1 = set([x.lower() for x in case1.get("Ingredientes_prohibidos", [])])
        s2 = set([x.lower() for x in case2.get("Ingredientes_prohibidos", [])])
        union = len(s1 | s2)
        inter = len(s1 & s2)
        ing_sim = inter / union if union > 0 else 1
        score += ing_sim * w["Forbidden"]

        return score

    def retrieve_top(self, new_case, top_n=3):
        scored = []

        print("\n[RETRIEVE] Computing similarities...")
        for case in self.case_base:
            score = self.similarity(new_case, case["problem"])
            print(f"   - Case {case['id']} -> Score: {score:.4f}")
            scored.append((case, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        scored = scored[:top_n]

        total = sum(s for _, s in scored)
        if total <= 0:
            # if all scores are zero, give equal probability
            normalized = [(c, 1 / len(scored)) for c, _ in scored] if scored else []
        else:
            normalized = [(c, s / total) for c, s in scored]

        print(f"[RETRIEVE] Retrieved top {len(normalized)} cases.")
        return normalized

class Reuser:
    def reuse_w(self, retrieved_cases, rejects=None):
        print("[REUSE] Creating possible solution.")

        new_case = {"Platos": {
            "Primero": {"Nombre": ""},
            "Segundo": {"Nombre": ""},
            "Postre": {"Nombre": ""}
        }}

        for course in new_case["Platos"].keys():

            adjusted_cases = []

            for case, weight in retrieved_cases:
                # handle empty or missing dish names gracefully
                dish_name = case["solution"]["Platos"].get(course, {}).get("Nombre", "")
                penalty = 1.0

                # ----------------------------------------
                # APPLY USER FEEDBACK / REJECTION REASON
                # ----------------------------------------
                if rejects:
                    for rejected_solution, reason in rejects:
                        reason = reason.lower()

                        # ❌ User rejected this specific course
                        if reason == course.lower():
                            bad_dish = rejected_solution["Platos"][course]["Nombre"]
                            if dish_name == bad_dish:
                                penalty = 0  # hard reject this dish

                        # ⚠️ User disliked something else, but not this course
                        elif reason in ("primero", "segundo", "postre"):
                            # No penalty for this course
                            continue

                        # ⚠️ "otros" → dislike whole menu → apply soft global penalty
                        elif reason == "otros":
                            penalty *= 0.5

                if penalty > 0 and dish_name:
                    adjusted_cases.append((case, weight * penalty))

            if not adjusted_cases:
                print(f"[REUSE] No valid cases for course '{course}' after rejection filtering.")
                return None

            # ----------------------------------------
            # SAMPLE DISH BASED ON ADJUSTED WEIGHTS
            # ----------------------------------------
            dishes = [c["solution"]["Platos"][course]["Nombre"] for c, _ in adjusted_cases]
            weights = [w for _, w in adjusted_cases]

            total = sum(weights)
            if total <= 0:
                weights = [1/len(weights)] * len(weights)
            else:
                weights = [w / total for w in weights]

            selected = random.choices(dishes, weights=weights, k=1)[0]
            new_case["Platos"][course]["Nombre"] = selected

        return new_case

class Reviser:
    def __init__(self, reuser):
        self.reuser = reuser

    def revise(self, proposed_solution, query, alternatives, rejects=None):

        if proposed_solution is None:
            print("[REVISE] No further solutions possible.")
            return None

        print("\n[REVISE] Proposed Menu:")
        print(json.dumps(proposed_solution, indent=2, ensure_ascii=False))

        # Interactive: ask user to accept or not
        try:
            feedback = input("Do you accept this menu? ([Y]/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            # if running non-interactively, accept by default
            feedback = 'y'

        if feedback == 'n':
            print("[REVISE] Solution rejected.")
            try:
                feedback_reason = input("What was wrong with the menu? (Primero, Segundo, Postre, Otros): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                feedback_reason = "otros"
            rejects = rejects + [(proposed_solution, feedback_reason)] if rejects else [(proposed_solution, feedback_reason)]
            new_solution = self.reuser.reuse_w(alternatives, rejects)
            return self.revise(new_solution, query, alternatives, rejects)

        print("[REVISE] Accepted final solution.")
        return proposed_solution

class Retainer:
    def __init__(self, case_base):
        self.case_base = case_base

    def retain(self, problem, solution):
        new_id = len(self.case_base) + 1
        new_case = {
            "id": new_id,
            "problem": problem,
            "solution": solution
        }
        self.case_base.append(new_case)
        print(f"[RETAIN] Stored new case ID {new_id}.")
        return new_case

# ============================================================
# MenuCBR: loads both toy cases and converted dataclass cases
# ============================================================

class MenuCBR:
    def __init__(self):
        self.case_base = []
        self._load_toy_data()

        self.retriever = Retriever(self.case_base)
        self.reuser = Reuser()
        self.reviser = Reviser(self.reuser)
        self.retain_module = Retainer(self.case_base)

    def _load_toy_data(self):
        # --- Original toy cases (kept for variety) ---
        case_1 = {
            "id": 1,
            "problem": {
                "Tipo_de_Evento": "Boda",
                "Estación_Evento": "Verano",
                "Número_comensales": 80,
                "Grupo_Dietario": "Omnívoro",
                "Ingredientes_prohibidos": ["Mariscos"]
            },
            "solution": {
                "Platos": {
                    "Primero": {"Nombre": "Ensalada de quinoa"},
                    "Segundo": {"Nombre": "Filete de ternera"},
                    "Postre": {"Nombre": "Tarta de frutas"}
                }
            }
        }

        case_2 = {
            "id": 2,
            "problem": {
                "Tipo_de_Evento": "Corporativo",
                "Estación_Evento": "Invierno",
                "Número_comensales": 200,
                "Grupo_Dietario": "Vegetariano",
                "Ingredientes_prohibidos": ["Nueces"]
            },
            "solution": {
                "Platos": {
                    "Primero": {"Nombre": "Crema de calabaza"},
                    "Segundo": {"Nombre": "Lasaña de espinacas"},
                    "Postre": {"Nombre": "Brownie vegano"}
                }
            }
        }

        case_3 = {
            "id": 3,
            "problem": {
                "Tipo_de_Evento": "Cumpleaños",
                "Estación_Evento": "Primavera",
                "Número_comensales": 20,
                "Grupo_Dietario": "Omnívoro",
                "Ingredientes_prohibidos": ["Picante"]
            },
            "solution": {
                "Platos": {
                    "Primero": {"Nombre": "Palitos de mozzarella"},
                    "Segundo": {"Nombre": "Mini hamburguesas"},
                    "Postre": {"Nombre": "Helado de vainilla"}
                }
            }
        }

        # Append the original toy cases
        self.case_base.extend([case_1, case_2, case_3])

        # --- Add complex dataclass cases, converted to simple dict format ---
        complex_case = example_case(case_id="case_complex_001")
        simple_case = convert_case_to_simple_dict(complex_case)
        # ensure numeric id for uniformity with toy cases (or keep string id)
        # We'll append as-is (id will be string), prototype uses it only for printing
        self.case_base.append(simple_case)

        # (Optional) Add another modified complex case for variety
        complex_case2 = example_case(case_id="case_complex_002")
        # tweak some fields to diversify
        complex_case2.context.season = "Verano"
        complex_case2.context.number_of_guests = 60
        complex_case2.client_profile.dietary_restrictions = ["Sin frutos secos"]
        simple_case2 = convert_case_to_simple_dict(complex_case2)
        self.case_base.append(simple_case2)

    def solve(self, query):
        print(f"\n======== NEW QUERY: {query['Tipo_de_Evento']} / {query['Grupo_Dietario']} ========")

        retrieved_cases = self.retriever.retrieve_top(query, top_n=3)
        if not retrieved_cases:
            print("[CBR] No retrieved cases, cannot propose solution.")
            return None

        candidate = self.reuser.reuse_w(retrieved_cases, rejects=None)
        revised = self.reviser.revise(candidate, query, retrieved_cases)

        if revised is not None:
            self.retain_module.retain(query, revised)

        return revised

# ============================================================
# Execution example (interactive by default; non-interactive fallback)
# ============================================================

if __name__ == "__main__":
    cbr = MenuCBR()

    query = {
        "Tipo_de_Evento": "Boda",
        "Estación_Evento": "Verano",
        "Número_comensales": 60,
        "Grupo_Dietario": "Omnívoro",
        "Ingredientes_prohibidos": ["Mariscos"]
    }

    result = cbr.solve(query)

    print("\n--- FINAL RECOMMENDED MENU ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n--- CASES IN MEMORY: {len(cbr.case_base)} ---")
