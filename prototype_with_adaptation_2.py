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
    prep_time: str

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
    role: str

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
# JUSTIFICATION
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
# OUTCOME
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
        return json.dumps({cid: asdict(c) for cid, c in self.cases.items()},
                          indent=4, ensure_ascii=False)


CASE_BASE = CaseBase()

# ============================================================
# ADAPTATION ENGINE WITH MEANINGFUL RENAMING
# ============================================================

class AdaptationEngine:

    @staticmethod
    def meaningful_dish_suffix(context: Context, client: ClientProfile) -> str:
        """Create a human-readable adaptation descriptor."""
        tags = []

        if "vegan" in client.dietary_restrictions:
            tags.append("Vegan Adaptation")
        elif "vegetarian" in client.dietary_restrictions:
            tags.append("Vegetarian Adaptation")
        elif "gluten-free" in client.dietary_restrictions:
            tags.append("Gluten-Free Adaptation")

        if client.health_goals == "light":
            tags.append("Light Version")

        if client.experience_level == "adventurous":
            tags.append("Fermentation/Experimental Twist")

        if context.season:
            tags.append(f"Seasonal {context.season.capitalize()} Touch")

        return " • ".join(tags)

    @staticmethod
    def rename_dishes(menu: Menu, suffix: str):
        for dish in menu.courses:
            dish.dish_name = f"{dish.dish_name} ({suffix})"

    @staticmethod
    def apply_rules(context: Context, client: ClientProfile, style: StyleProfile):
        """Generate brand new dishes via rules."""

        dishes = []

        # Decide seasonal ingredient
        seasonal_map = {
            "winter": "pumpkin",
            "summer": "melon",
            "spring": "asparagus",
            "autumn": "mushroom"
        }
        seasonal = seasonal_map.get(context.season, "seasonal vegetable")

        # Lower-fat if needed
        fat_source = "olive oil spray" if client.health_goals == "light" else "butter"

        # Adventurous techniques
        adventurous_tech = ["fermentation", "foam"] if client.experience_level == "adventurous" else []

        # Starter
        dishes.append(
            Dish(
                course_type="starter",
                dish_name="Mediterranean Seasonal Starter",
                ingredients=[
                    Ingredient("tomato", "main"),
                    Ingredient(seasonal, "secondary"),
                    Ingredient("basil", "aroma")
                ],
                techniques=["steam"] + adventurous_tech,
                cultural_influence=client.cultural_affinities,
                presentation_notes="vertical minimalist plating"
            )
        )

        # Main
        dishes.append(
            Dish(
                course_type="main",
                dish_name="Fusion Light Main Course",
                ingredients=[
                    Ingredient("white fish", "main"),
                    Ingredient(seasonal, "secondary"),
                    Ingredient(fat_source, "fat")
                ],
                techniques=["sous-vide"] + adventurous_tech,
                cultural_influence=client.cultural_affinities,
                presentation_notes="nordic structure with clean geometry"
            )
        )

        # Dessert
        dessert_main = "citrus" if "citrus" in client.flavor_preferences.likes else "berries"

        dishes.append(
            Dish(
                course_type="dessert",
                dish_name="Aromatic Herbal Dessert",
                ingredients=[
                    Ingredient(dessert_main, "main"),
                    Ingredient("almond milk", "fat"),
                    Ingredient("herbal garnish", "aroma")
                ],
                techniques=["infusion", "chill"],
                cultural_influence=["Fusion"],
                presentation_notes="air-light finish with herbal aroma"
            )
        )

        return Menu(courses=dishes)

    @staticmethod
    def generate_justification(context: Context, client: ClientProfile, style: StyleProfile):

        major_adaptations = []

        if client.health_goals == "light":
            major_adaptations.append("Reduced fats using olive oil spray instead of butter.")

        if "gluten-free" in client.dietary_restrictions:
            major_adaptations.append("Ensured all sauces/ingredients were gluten-free.")

        if client.experience_level == "adventurous":
            major_adaptations.append("Added fermentation and foam for sensory exploration.")

        major_adaptations.append(f"Included seasonal ingredient: {context.season} produce.")

        causals = [
            CausalLink("Light health goal", "steam + sous-vide + reduced fats"),
            CausalLink("Adventurous profile", "fermentation/foam techniques"),
            CausalLink("Seasonal constraints", "use of seasonal vegetables")
        ]

        return Justification(
            why_this_menu=[
                "Menu adapted based on health goals, season, and adventurous flavor profile.",
                f"Includes techniques aligned with chef inspirations {style.chef_inspiration}.",
                "Respects cultural affinities and dietary constraints."
            ],
            causal_links=causals,
            major_adaptations=major_adaptations
        )


# ============================================================
# CASE GENERATION PIPELINE
# ============================================================

def generate_new_case(base_context: Context, base_client: ClientProfile, base_style: StyleProfile):
    case_id = f"case_{str(uuid.uuid4())[:8]}"

    menu = AdaptationEngine.apply_rules(base_context, base_client, base_style)

    # NEW: generate *meaningful* suffix
    suffix = AdaptationEngine.meaningful_dish_suffix(base_context, base_client)
    AdaptationEngine.rename_dishes(menu, suffix)

    justification = AdaptationEngine.generate_justification(base_context, base_client, base_style)

    outcome = Outcome(
        client_satisfaction=0.0,
        guest_comments=[],
        success_metrics={"placeholder": False},
        adaptation_difficulties=[]
    )

    new_case = CulinaryCase(
        id=case_id,
        context=base_context,
        client_profile=base_client,
        style_profile=base_style,
        menu=menu,
        justification=justification,
        outcome=outcome
    )

    # Store case
    CASE_BASE.add_case(new_case)

    return new_case


# ============================================================
# EXECUTION EXAMPLE
# ============================================================

if __name__ == "__main__":

    new_case = generate_new_case(
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
            flavor_preferences=FlavorPreferences(likes=["citrus", "umami"], dislikes=["bitter"]),
            cultural_affinities=["Mediterranean", "Japanese"],
            health_goals="light",
            experience_level="adventurous"
        ),
        base_style=StyleProfile(
            chef_inspiration=["Ferran Adrià", "Noma"],
            culinary_tradition=["Catalan", "Nordic"],
            techniques_emphasized=["fermentation", "foams", "sous-vide"],
            presentation_style="minimalist",
            sensory_goals=SensoryGoals(texture=["creamy", "crunchy"],
                                      aromatic_profile=["herbal", "citrus"])
        )
    )

    print("=== ADAPTED CASE ===")
    print(json.dumps(asdict(new_case), indent=4, ensure_ascii=False))

    print("\n=== CASE BASE (ALL STORED CASES) ===")
    print(CASE_BASE.to_json())
