#!/usr/bin/env python3
# integrated_cbr_full.py
# Full prototype: uses the dataclass CulinaryCase representation (all fields),
# generates new toy cases from it, converts to simple format, and runs CBR.

import json
import random
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

# -----------------------------
# Your case dataclasses (same as provided)
# -----------------------------
EVENT_TYPES = ["wedding", "congress", "family_event", "gala", "corporate"]
BUDGET_LEVELS = ["low", "medium", "high", "premium"]
FORMALITY_LEVELS = ["casual", "semi-formal", "formal"]
HEALTH_GOALS = ["light", "high-protein", "low-salt"]
EXPERIENCE_LEVELS = ["traditional", "adventurous", "experimental"]
COURSE_TYPES = ["starter", "main", "dessert"]


@dataclass
class EventLocation:
    country: str
    region: str

@dataclass
class TimeConstraints:
    prep_time: str  # "short", "medium", "long"


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


# -----------------------------
# Conversion: CulinaryCase -> simple prototype dict (Spanish keys)
# -----------------------------
def convert_case_to_simple_dict(culinary_case: CulinaryCase) -> dict:
    """
    Convert a CulinaryCase dataclass to the simple dict structure used by the prototype.
    We include many fields from the case so the Retriever can use them.
    """
    # Problem fields
    # Grupo_Dietario: join dietary restrictions (could be multiple)
    grupo = ", ".join(culinary_case.client_profile.dietary_restrictions) if culinary_case.client_profile.dietary_restrictions else "Omnívoro"

    # Ingredients forbidden: here we take client's dislikes as proxies for forbidden ingredients
    ingredientes_prohibidos = culinary_case.client_profile.flavor_preferences.dislikes or []

    # Culinary style: flatten lists to allow similarity on traditions/techniques
    culinary_tradition = culinary_case.style_profile.culinary_tradition or []
    techniques = culinary_case.style_profile.techniques_emphasized or []
    presentation = culinary_case.style_profile.presentation_style or ""
    sensory = culinary_case.style_profile.sensory_goals.texture + culinary_case.style_profile.sensory_goals.aromatic_profile

    simple_problem = {
        "Tipo_de_Evento": culinary_case.context.event_type,
        "Estación_Evento": culinary_case.context.season,
        "Número_comensales": culinary_case.context.number_of_guests,
        "Grupo_Dietario": grupo,
        "Ingredientes_prohibidos": ingredientes_prohibidos,
        # Extended fields for richer similarity
        "Prep_Time": culinary_case.context.time_constraints.prep_time,
        "Available_Ingredients": culinary_case.context.available_ingredients,
        "Culinary_Tradition": culinary_tradition,
        "Techniques": techniques,
        "Presentation_Style": presentation,
        "Sensory_Goals": sensory,
        "Cultural_Affinities": culinary_case.client_profile.cultural_affinities
    }

    # Solution part (Platos): map starter/main/dessert -> Primero/Segundo/Postre
    course_map = {"starter": "Primero", "main": "Segundo", "dessert": "Postre"}
    platos = {}
    for dish in culinary_case.menu.courses:
        spanish = course_map.get(dish.course_type, dish.course_type)
        platos[spanish] = {"Nombre": dish.dish_name}

    # ensure keys
    for k in ("Primero", "Segundo", "Postre"):
        if k not in platos:
            platos[k] = {"Nombre": ""}

    simple_case = {
        "id": culinary_case.id,
        "problem": simple_problem,
        "solution": {"Platos": platos}
    }
    return simple_case


# -----------------------------
# Retriever (uses many features now)
# -----------------------------
class Retriever:
    def __init__(self, case_base):
        self.case_base = case_base

        # New weight configuration (sum should be <= 1; remaining weight is flexible)
        self.weights = {
            "Tipo": 0.18,
            "Estacion": 0.12,
            "Diet": 0.15,
            "Pax": 0.08,
            "Forbidden": 0.10,
            "Prep": 0.06,
            "Tradition": 0.10,
            "Techniques": 0.08,
            "Presentation": 0.06,
            "Sensory": 0.07
        }

    @staticmethod
    def jaccard(a, b):
        if not a and not b:
            return 1.0
        s1 = set([x.lower() for x in a])
        s2 = set([x.lower() for x in b])
        inter = len(s1 & s2)
        union = len(s1 | s2)
        return inter / union if union > 0 else 0.0

    def similarity(self, query: dict, case_problem: dict) -> float:
        """
        Query and case_problem are the simple dicts (from convert_case_to_simple_dict)
        We compute a weighted similarity using many fields of the case.
        """
        score = 0.0
        w = self.weights

        # Event type (exact)
        if query.get("Tipo_de_Evento", "").lower() == case_problem.get("Tipo_de_Evento", "").lower():
            score += w["Tipo"]

        # Season
        if query.get("Estación_Evento", "").lower() == case_problem.get("Estación_Evento", "").lower():
            score += w["Estacion"]

        # Dietary: compare dietary groups (string of comma separated values)
        q_diets = set([s.strip().lower() for s in query.get("Grupo_Dietario", "").split(",") if s.strip()])
        c_diets = set([s.strip().lower() for s in case_problem.get("Grupo_Dietario", "").split(",") if s.strip()])
        if q_diets or c_diets:
            inter = len(q_diets & c_diets)
            union = len(q_diets | c_diets)
            diet_sim = inter / union if union > 0 else 0.0
            score += diet_sim * w["Diet"]
        else:
            score += w["Diet"] * 0.5

        # Pax similarity (scaled)
        q_pax = int(query.get("Número_comensales", 0))
        c_pax = int(case_problem.get("Número_comensales", 0))
        diff = abs(q_pax - c_pax)
        pax_sim = max(0, 1 - diff / 500)
        score += pax_sim * w["Pax"]

        # Forbidden ingredients similarity (we want lower overlap of forbidden -> lower score)
        # But as in previous prototype we treat intersection as similarity of constraints, so keep that behavior
        q_forbidden = set([s.lower() for s in query.get("Ingredientes_prohibidos", [])])
        c_forbidden = set([s.lower() for s in case_problem.get("Ingredientes_prohibidos", [])])
        union = len(q_forbidden | c_forbidden)
        inter = len(q_forbidden & c_forbidden)
        ing_sim = inter / union if union > 0 else 1.0
        score += ing_sim * w["Forbidden"]

        # Prep time (exact match gets full weight, otherwise partial)
        if query.get("Prep_Time", "").lower() == case_problem.get("Prep_Time", "").lower():
            score += w["Prep"]

        # Culinary tradition (jaccard)
        tradition_sim = self.jaccard(query.get("Culinary_Tradition", []), case_problem.get("Culinary_Tradition", []))
        score += tradition_sim * w["Tradition"]

        # Techniques similarity (jaccard)
        tech_sim = self.jaccard(query.get("Techniques", []), case_problem.get("Techniques", []))
        score += tech_sim * w["Techniques"]

        # Presentation style (exact or partial)
        if query.get("Presentation_Style", "").lower() == case_problem.get("Presentation_Style", "").lower():
            score += w["Presentation"]

        # Sensory goals similarity (treat as set)
        sensory_sim = self.jaccard(query.get("Sensory_Goals", []), case_problem.get("Sensory_Goals", []))
        score += sensory_sim * w["Sensory"]

        return score

    def retrieve_top(self, new_case, top_n=3):
        scored = []
        print("\n[RETRIEVE] Computing similarities (using full case fields)...")
        for case in self.case_base:
            score = self.similarity(new_case, case["problem"])
            print(f"   - Case {case['id']} -> Score: {score:.4f}")
            scored.append((case, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:top_n]

        total = sum(s for _, s in top)
        if total <= 0:
            normalized = [(c, 1 / len(top)) for c, _ in top] if top else []
        else:
            normalized = [(c, s / total) for c, s in top]

        print(f"[RETRIEVE] Retrieved top {len(normalized)} cases.")
        return normalized


# -----------------------------
# Reuser, Reviser, Retainer (unchanged logic, only expect 'Platos' format)
# -----------------------------
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
                dish_name = case["solution"]["Platos"].get(course, {}).get("Nombre", "")
                penalty = 1.0

                if rejects:
                    for rejected_solution, reason in rejects:
                        reason = reason.lower()

                        if reason == course.lower():
                            bad_dish = rejected_solution["Platos"][course]["Nombre"]
                            if dish_name == bad_dish:
                                penalty = 0

                        elif reason in ("primero", "segundo", "postre"):
                            continue

                        elif reason == "otros":
                            penalty *= 0.5

                if penalty > 0 and dish_name:
                    adjusted_cases.append((case, weight * penalty))

            if not adjusted_cases:
                print(f"[REUSE] No valid cases for course '{course}' after rejection filtering.")
                return None

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

        try:
            feedback = input("Do you accept this menu? ([Y]/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
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


# -----------------------------
# MenuCBR: loads NEW toy data constructed from CulinaryCase (no old toy cases)
# -----------------------------
class MenuCBR:
    def __init__(self):
        self.case_base = []
        self._load_toy_data()

        self.retriever = Retriever(self.case_base)
        self.reuser = Reuser()
        self.reviser = Reviser(self.reuser)
        self.retain_module = Retainer(self.case_base)

    def _load_toy_data(self):
        # Create a diverse set of new toy cases using the dataclasses.
        cases = []

        # Case A: formal wedding, winter, Mediterranean-Japanese fusion
        cA = CulinaryCase(
            id="A",
            context=Context(
                event_type="wedding",
                season="winter",
                location=EventLocation(country="Spain", region="Catalonia"),
                number_of_guests=120,
                budget_level="high",
                formality_level="formal",
                available_ingredients=["artichoke", "lemon", "sea bass", "almonds"],
                time_constraints=TimeConstraints(prep_time="long")
            ),
            client_profile=ClientProfile(
                dietary_restrictions=["gluten-free"],
                flavor_preferences=FlavorPreferences(likes=["citrus", "umami"], dislikes=["bitter"]),
                cultural_affinities=["Mediterranean", "Japanese"],
                health_goals="light",
                experience_level="adventurous"
            ),
            style_profile=StyleProfile(
                chef_inspiration=["Ferran Adrià"],
                culinary_tradition=["Catalan", "Nordic"],
                techniques_emphasized=["fermentation", "foams", "sous-vide"],
                presentation_style="minimalist",
                sensory_goals=SensoryGoals(texture=["creamy", "crunchy"], aromatic_profile=["herbal", "citrus"])
            ),
            menu=Menu(courses=[
                Dish(course_type="starter", dish_name="Artichoke Textures with Citrus Foam",
                     ingredients=[Ingredient("artichoke","main"), Ingredient("lemon","aroma"), Ingredient("olive oil","fat")],
                     techniques=["roasting","emulsion","foam"],
                     cultural_influence=["Mediterranean"],
                     presentation_notes="vertical plating with foam"),
                Dish(course_type="main", dish_name="Miso-Glazed Sea Bass with Fermented Barley",
                     ingredients=[Ingredient("sea bass","main"), Ingredient("miso","seasoning"), Ingredient("barley","base")],
                     techniques=["glazing","fermentation","slow-cook"],
                     cultural_influence=["Japanese"],
                     presentation_notes="minimalist plate"),
                Dish(course_type="dessert", dish_name="Citrus Almond Cream",
                     ingredients=[Ingredient("citrus blend","main"), Ingredient("almond","fat"), Ingredient("herbs","aroma")],
                     techniques=["infusion","whipping"],
                     cultural_influence=["Fusion"],
                     presentation_notes="creamy mousse with crunchy top")
            ]),
            justification=Justification(
                why_this_menu=["seasonal produce","fusion preferences","formal plating"],
                causal_links=[CausalLink("winter","warm dishes")],
                major_adaptations=["tamari for soy sauce"]
            ),
            outcome=Outcome(4.7, ["delicious"], {"budget_compliance":True}, ["none"])
        )
        cases.append(cA)

        # Case B: corporate gala, summer, Mediterranean traditional
        cB = CulinaryCase(
            id="B",
            context=Context(
                event_type="gala",
                season="summer",
                location=EventLocation(country="France", region="Paris"),
                number_of_guests=250,
                budget_level="premium",
                formality_level="formal",
                available_ingredients=["foie gras", "strawberries", "truffles"],
                time_constraints=TimeConstraints(prep_time="long")
            ),
            client_profile=ClientProfile(
                dietary_restrictions=["no_pork"],
                flavor_preferences=FlavorPreferences(likes=["umami"], dislikes=[]),
                cultural_affinities=["French"],
                health_goals=None,
                experience_level="traditional"
            ),
            style_profile=StyleProfile(
                chef_inspiration=["Bocuse"],
                culinary_tradition=["French"],
                techniques_emphasized=["sous-vide","roasting"],
                presentation_style="elegant",
                sensory_goals=SensoryGoals(texture=["silky"], aromatic_profile=["herbal"])
            ),
            menu=Menu(courses=[
                Dish(course_type="starter", dish_name="Foie Terrine with Seasonal Jam",
                     ingredients=[Ingredient("foie gras","main"), Ingredient("jam","sweet")],
                     techniques=["terrine","preserve"],
                     cultural_influence=["French"],
                     presentation_notes="classic"),
                Dish(course_type="main", dish_name="Roast Sirloin with Truffle Jus",
                     ingredients=[Ingredient("beef","main"), Ingredient("truffle","aroma")],
                     techniques=["roasting","sauce-making"],
                     cultural_influence=["French"],
                     presentation_notes="plated elegantly"),
                Dish(course_type="dessert", dish_name="Strawberry Millefeuille",
                     ingredients=[Ingredient("strawberries","main"), Ingredient("cream","fat")],
                     techniques=["lamination","assembly"],
                     cultural_influence=["French"],
                     presentation_notes="layered dessert")
            ]),
            justification=Justification(["premium ingredients","formal event"], [], []),
            outcome=Outcome(4.9, ["excellent"], {"budget_compliance":True}, [])
        )
        cases.append(cB)

        # Case C: family event, spring, casual, vegetarian
        cC = CulinaryCase(
            id="C",
            context=Context(
                event_type="family_event",
                season="spring",
                location=EventLocation(country="USA", region="California"),
                number_of_guests=30,
                budget_level="medium",
                formality_level="casual",
                available_ingredients=["tomato","basil","mozzarella","bread"],
                time_constraints=TimeConstraints(prep_time="short")
            ),
            client_profile=ClientProfile(
                dietary_restrictions=["vegetarian"],
                flavor_preferences=FlavorPreferences(likes=["fresh","acidic"], dislikes=["spicy"]),
                cultural_affinities=["Italian"],
                health_goals="light",
                experience_level="traditional"
            ),
            style_profile=StyleProfile(
                chef_inspiration=["home_cook"],
                culinary_tradition=["Italian"],
                techniques_emphasized=["fresh assembly","grilling"],
                presentation_style="rustic",
                sensory_goals=SensoryGoals(texture=["fresh","crunchy"], aromatic_profile=["herbal"])
            ),
            menu=Menu(courses=[
                Dish(course_type="starter", dish_name="Tomato Basil Bruschetta",
                     ingredients=[Ingredient("tomato","main"), Ingredient("basil","aroma"), Ingredient("bread","base")],
                     techniques=["toasting","assembly"],
                     cultural_influence=["Italian"],
                     presentation_notes="rustic toast"),
                Dish(course_type="main", dish_name="Grilled Vegetable Lasagna",
                     ingredients=[Ingredient("zucchini","main"), Ingredient("cheese","fat")],
                     techniques=["grilling","baking"],
                     cultural_influence=["Italian"],
                     presentation_notes="family style"),
                Dish(course_type="dessert", dish_name="Lemon Olive Oil Cake",
                     ingredients=[Ingredient("lemon","main"), Ingredient("olive oil","fat")],
                     techniques=["baking"],
                     cultural_influence=["Mediterranean"],
                     presentation_notes="simple cake")
            ]),
            justification=Justification(["family friendly","fresh"], [], []),
            outcome=Outcome(4.5, ["kids loved it"], {"budget_compliance":True}, [])
        )
        cases.append(cC)

        # Case D: congress lunch, autumn, multicultural, quick prep
        cD = CulinaryCase(
            id="D",
            context=Context(
                event_type="congress",
                season="autumn",
                location=EventLocation(country="Germany", region="Berlin"),
                number_of_guests=150,
                budget_level="medium",
                formality_level="semi-formal",
                available_ingredients=["potato","carrot","lentils"],
                time_constraints=TimeConstraints(prep_time="short")
            ),
            client_profile=ClientProfile(
                dietary_restrictions=["vegan"],
                flavor_preferences=FlavorPreferences(likes=["hearty"], dislikes=[]),
                cultural_affinities=["International"],
                health_goals=None,
                experience_level="experimental"
            ),
            style_profile=StyleProfile(
                chef_inspiration=["casual_chefs"],
                culinary_tradition=["Fusion"],
                techniques_emphasized=["stewing","quick-pickles"],
                presentation_style="accessible",
                sensory_goals=SensoryGoals(texture=["hearty"], aromatic_profile=["smoky"])
            ),
            menu=Menu(courses=[
                Dish(course_type="starter", dish_name="Spiced Lentil Soup",
                     ingredients=[Ingredient("lentils","main"), Ingredient("carrot","vegetable")],
                     techniques=["stewing"],
                     cultural_influence=["Middle Eastern"],
                     presentation_notes="bowl service"),
                Dish(course_type="main", dish_name="Roasted Root Vegetable Bowl",
                     ingredients=[Ingredient("potato","main"), Ingredient("beet","vegetable")],
                     techniques=["roasting"],
                     cultural_influence=["Fusion"],
                     presentation_notes="bowl"),
                Dish(course_type="dessert", dish_name="Apple Compote",
                     ingredients=[Ingredient("apple","main"), Ingredient("cinnamon","aroma")],
                     techniques=["stewing"],
                     cultural_influence=["European"],
                     presentation_notes="simple serving")
            ]),
            justification=Justification(["quick to serve","vegan-friendly"], [], []),
            outcome=Outcome(4.3, ["good"], {"timeliness":True}, [])
        )
        cases.append(cD)

        # Case E: intimate experimental dinner, autumn, adventurous
        cE = CulinaryCase(
            id="E",
            context=Context(
                event_type="gala",
                season="autumn",
                location=EventLocation(country="Japan", region="Tokyo"),
                number_of_guests=12,
                budget_level="high",
                formality_level="semi-formal",
                available_ingredients=["miso","seaweed","daikon"],
                time_constraints=TimeConstraints(prep_time="long")
            ),
            client_profile=ClientProfile(
                dietary_restrictions=[],
                flavor_preferences=FlavorPreferences(likes=["umami","fermented"], dislikes=[]),
                cultural_affinities=["Japanese"],
                health_goals=None,
                experience_level="experimental"
            ),
            style_profile=StyleProfile(
                chef_inspiration=["modern_chefs"],
                culinary_tradition=["Japanese","Nordic"],
                techniques_emphasized=["fermentation","smoking"],
                presentation_style="artistic",
                sensory_goals=SensoryGoals(texture=["delicate","textured"], aromatic_profile=["umami","smoky"])
            ),
            menu=Menu(courses=[
                Dish(course_type="starter", dish_name="Miso Foam with Seaweed Crisp",
                     ingredients=[Ingredient("miso","seasoning"), Ingredient("seaweed","crisp")],
                     techniques=["foam","dehydration"],
                     cultural_influence=["Japanese"],
                     presentation_notes="small amuse-bouche"),
                Dish(course_type="main", dish_name="Smoked Daikon with Barley",
                     ingredients=[Ingredient("daikon","main"), Ingredient("barley","base")],
                     techniques=["smoking","braise"],
                     cultural_influence=["Fusion"],
                     presentation_notes="minimalist plate"),
                Dish(course_type="dessert", dish_name="Green Tea Air",
                     ingredients=[Ingredient("matcha","main"), Ingredient("milk","fat")],
                     techniques=["molecular","whipping"],
                     cultural_influence=["Japanese"],
                     presentation_notes="airy dessert")
            ]),
            justification=Justification(["experimental","umami focus"], [], []),
            outcome=Outcome(4.8, ["imaginative"], {"guest_satisfaction":True}, [])
        )
        cases.append(cE)

        # Convert all culinary cases to simple dicts and store in case_base
        for c in cases:
            simple = convert_case_to_simple_dict(c)
            self.case_base.append(simple)

    def solve(self, query):
        print(f"\n======== NEW QUERY: {query.get('Tipo_de_Evento','?')} / {query.get('Grupo_Dietario','?')} ========")
        retrieved_cases = self.retriever.retrieve_top(query, top_n=3)
        if not retrieved_cases:
            print("[CBR] No retrieved cases, cannot propose solution.")
            return None

        candidate = self.reuser.reuse_w(retrieved_cases, rejects=None)
        revised = self.reviser.revise(candidate, query, retrieved_cases)

        if revised is not None:
            self.retain_module.retain(query, revised)

        return revised


# -----------------------------
# Demo: run with an example query that uses many fields
# -----------------------------
if __name__ == "__main__":
    # Build a rich query dict with the same extended fields used in conversion
    query = {
        "Tipo_de_Evento": "wedding",
        "Estación_Evento": "winter",
        "Número_comensales": 100,
        "Grupo_Dietario": "gluten-free",
        "Ingredientes_prohibidos": ["nuts"],
        "Prep_Time": "long",
        "Available_Ingredients": ["artichoke", "lemon", "olive oil"],
        "Culinary_Tradition": ["Catalan", "Mediterranean"],
        "Techniques": ["fermentation", "foam"],
        "Presentation_Style": "minimalist",
        "Sensory_Goals": ["creamy", "citrus"],
        "Cultural_Affinities": ["Mediterranean", "Japanese"]
    }

    cbr = MenuCBR()
    result = cbr.solve(query)

    print("\n--- FINAL RECOMMENDED MENU ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n--- CASES IN MEMORY: {len(cbr.case_base)} ---")
