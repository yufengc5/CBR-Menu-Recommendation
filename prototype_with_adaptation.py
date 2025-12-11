from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
import json
import uuid

# ============================================================
# CONSTANTS
# ============================================================

EVENT_TYPES = ["wedding", "congress", "family_event", "gala", "corporate"]
BUDGET_LEVELS = ["low", "medium", "high", "premium"]
FORMALITY_LEVELS = ["casual", "semi-formal", "formal"]
HEALTH_GOALS = ["light", "high-protein", "low-salt"]
EXPERIENCE_LEVELS = ["traditional", "adventurous", "experimental"]
COURSE_TYPES = ["starter", "main", "dessert"]

# ============================================================
# CONTEXT LAYER
# ============================================================

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
    time_constraints: TimeConstraints

# ============================================================
# CLIENT PROFILE LAYER
# ============================================================

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

# ============================================================
# STYLE & GASTRONOMIC IDENTITY
# ============================================================

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

# ============================================================
# MENU STRUCTURE
# ============================================================

@dataclass
class Ingredient:
    name: str
    role: str  # e.g. "main", "secondary", "aroma", "fat"

@dataclass
class Dish:
    course_type: str
    dish_name: str
    ingredients: List[Ingredient]
    techniques: List[str]
    cultural_influence: List[str]
    presentation_notes: str

@dataclass
class Menu:
    courses: List[Dish]

# ============================================================
# JUSTIFICATION & CAUSAL KNOWLEDGE
# ============================================================

@dataclass
class CausalLink:
    cause: str
    effect: str

@dataclass
class Justification:
    why_this_menu: List[str]
    causal_links: List[CausalLink]
    major_adaptations: List[str]

# ============================================================
# OUTCOME LAYER
# ============================================================

@dataclass
class Outcome:
    client_satisfaction: float
    guest_comments: List[str]
    success_metrics: Dict[str, bool]
    adaptation_difficulties: List[str]

# ============================================================
# COMPLETE CASE
# ============================================================

@dataclass
class CulinaryCase:
    id: str
    context: Context
    client_profile: ClientProfile
    style_profile: StyleProfile
    menu: Menu
    justification: Justification
    outcome: Outcome

# ============================================================
# CASE BASE
# ============================================================

class CaseBase:
    def __init__(self):
        self.cases: Dict[str, CulinaryCase] = {}

    def add_case(self, culinary_case: CulinaryCase):
        self.cases[culinary_case.id] = culinary_case

    def get_all(self):
        return list(self.cases.values())

    def to_json(self):
        return json.dumps({cid: asdict(c) for cid, c in self.cases.items()}, indent=4, ensure_ascii=False)

CASE_BASE = CaseBase()

# ============================================================
# RULE ENGINE FOR ADAPTATION
# ============================================================

class AdaptationEngine:

    @staticmethod
    def rename_dishes(menu: Menu, unique_suffix: str):
        for dish in menu.courses:
            dish.dish_name += f" ({unique_suffix})"

    @staticmethod
    def apply_rules(context: Context, client: ClientProfile, style: StyleProfile):
        """
        Creates a brand new adapted menu.
        This is not a copy of the example — it's rule-generated.
        """

        dishes = []

        # --- Rule 1: Light health goal → reduce fats, use steam/sous-vide
        if client.health_goals == "light":
            main_technique = "steam"
            fat_substitution = "olive oil spray"
        else:
            main_technique = "roast"
            fat_substitution = "butter"

        # --- Rule 2: Cultural affinities guide ingredient cores
        if "Mediterranean" in client.cultural_affinities:
            starter_main = "tomato"
            starter_aroma = "basil"
        else:
            starter_main = "root vegetables"
            starter_aroma = "ginger"

        # --- Rule 3: Adventurous → include fermentation/foam
        extra_techniques = []
        if client.experience_level == "adventurous":
            extra_techniques.append("fermentation")
            extra_techniques.append("foam")

        # --- Rule 4: Seasonal ingredient injection
        if context.season == "winter":
            seasonal = "pumpkin"
        elif context.season == "summer":
            seasonal = "melon"
        else:
            seasonal = "asparagus"

        # Build starter
        dishes.append(
            Dish(
                course_type="starter",
                dish_name="Seasonal Essence Starter",
                ingredients=[
                    Ingredient(starter_main, "main"),
                    Ingredient(seasonal, "secondary"),
                    Ingredient(starter_aroma, "aroma")
                ],
                techniques=[main_technique] + extra_techniques,
                cultural_influence=client.cultural_affinities,
                presentation_notes="clean vertical plating with aromatic accent"
            )
        )

        # Build main
        dishes.append(
            Dish(
                course_type="main",
                dish_name="Cultural Fusion Main Plate",
                ingredients=[
                    Ingredient("white fish", "main"),
                    Ingredient(seasonal, "secondary"),
                    Ingredient(fat_substitution, "fat")
                ],
                techniques=["sous-vide"] + extra_techniques,
                cultural_influence=client.cultural_affinities,
                presentation_notes="minimalist nordic-inspired layout"
            )
        )

        # Build dessert
        dessert_main = "citrus" if "citrus" in client.flavor_preferences.likes else "berries"
        dishes.append(
            Dish(
                course_type="dessert",
                dish_name="Aromatic Light Dessert",
                ingredients=[
                    Ingredient(dessert_main, "main"),
                    Ingredient("almond milk", "fat"),
                    Ingredient("herbal garnish", "aroma")
                ],
                techniques=["infusion", "chill"],
                cultural_influence=["Fusion"],
                presentation_notes="airy mousse with clean herbal finish"
            )
        )

        return Menu(courses=dishes)

    @staticmethod
    def generate_justification(context: Context, client: ClientProfile, style: StyleProfile):
        why = [
            f"Health goal '{client.health_goals}' → lower-fat techniques (steam/sous-vide).",
            f"Cultural affinities {client.cultural_affinities} → Mediterranean/Nordic flavor foundations.",
            f"Season '{context.season}' → integration of seasonal ingredient.",
            f"Experience level '{client.experience_level}' → inclusion of adventurous techniques."
        ]

        causal = [
            CausalLink(cause="light health goal", effect="use of steam + reduced fats"),
            CausalLink(cause="adventurous profile", effect="added fermentation + foam"),
            CausalLink(cause=f"{context.season} season", effect="seasonal ingredient adaptation")
        ]

        adaptations = [
            "Fat substitutions applied (almond milk, olive oil spray)",
            "Starter flavor core adjusted to match affinities",
            "Cultural influences integrated into all courses"
        ]

        return Justification(why_this_menu=why, causal_links=causal, major_adaptations=adaptations)

# ============================================================
# MAIN CASE-GENERATION PIPELINE
# ============================================================

def generate_new_case(base_context: Context, base_client: ClientProfile, base_style: StyleProfile):
    new_id = f"case_{str(uuid.uuid4())[:8]}"

    # Generate adapted menu using rules
    menu = AdaptationEngine.apply_rules(base_context, base_client, base_style)

    # Ensure dish names are unique in the case base
    AdaptationEngine.rename_dishes(menu, unique_suffix=new_id)

    justification = AdaptationEngine.generate_justification(base_context, base_client, base_style)

    # Dummy outcome — normally filled after the event
    outcome = Outcome(
        client_satisfaction=0.0,
        guest_comments=[],
        success_metrics={"placeholder": False},
        adaptation_difficulties=[]
    )

    new_case = CulinaryCase(
        id=new_id,
        context=base_context,
        client_profile=base_client,
        style_profile=base_style,
        menu=menu,
        justification=justification,
        outcome=outcome
    )

    # Store persistently
    CASE_BASE.add_case(new_case)

    return new_case


# ============================================================
# USAGE EXAMPLE
# ============================================================

if __name__ == "__main__":
    # Re-use the example context but create a NEW adapted case
    example = generate_new_case(
        base_context=Context(
            event_type="wedding",
            season="winter",
            location=EventLocation(country="Spain", region="Catalonia"),
            number_of_guests=120,
            budget_level="high",
            formality_level="formal",
            time_constraints=TimeConstraints(prep_time="long")
        ),
        base_client=ClientProfile(
            dietary_restrictions=["gluten-free"],
            flavor_preferences=FlavorPreferences(likes=["citrus","umami"], dislikes=["bitter"]),
            cultural_affinities=["Mediterranean", "Japanese"],
            health_goals="light",
            experience_level="adventurous"
        ),
        base_style=StyleProfile(
            chef_inspiration=["Ferran Adrià", "Noma"],
            culinary_tradition=["Catalan", "Nordic"],
            techniques_emphasized=["fermentation","foams","sous-vide"],
            presentation_style="minimalist",
            sensory_goals=SensoryGoals(texture=["creamy","crunchy"], aromatic_profile=["herbal","citrus"])
        )
    )

    print(json.dumps(asdict(example), indent=4, ensure_ascii=False))

    print("\n=== CASE BASE ===")
    print(CASE_BASE.to_json())
