from dataclasses import dataclass, field
from typing import List, Dict, Optional

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
    available_ingredients: List[str]
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
# OUTCOME LAYER (Feedback for learning)
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
# EXAMPLE CASE (you can remove or modify)
# ============================================================

def example_case() -> CulinaryCase:
    return CulinaryCase(
        id="case_001",

        # ----------------------
        # CONTEXT
        # ----------------------
        context=Context(
            event_type="wedding",
            season="winter",
            location=EventLocation(
                country="Spain",
                region="Catalonia"
            ),
            number_of_guests=120,
            budget_level="high",
            formality_level="formal",
            available_ingredients=["artichoke", "lemon", "sea bass", "almonds"],
            time_constraints=TimeConstraints(
                prep_time="long"
            )
        ),

        # ----------------------
        # CLIENT PROFILE
        # ----------------------
        client_profile=ClientProfile(
            dietary_restrictions=["gluten-free"],
            flavor_preferences=FlavorPreferences(
                likes=["citrus", "umami"],
                dislikes=["bitter"]
            ),
            cultural_affinities=["Mediterranean", "Japanese"],
            health_goals="light",
            experience_level="adventurous"
        ),

        # ----------------------
        # STYLE PROFILE
        # ----------------------
        style_profile=StyleProfile(
            chef_inspiration=["Ferran Adrià", "Noma"],
            culinary_tradition=["Catalan", "Nordic"],
            techniques_emphasized=["fermentation", "foams", "sous-vide"],
            presentation_style="minimalist",
            sensory_goals=SensoryGoals(
                texture=["creamy", "crunchy"],
                aromatic_profile=["herbal", "citrus"]
            )
        ),

        # ----------------------
        # MENU
        # ----------------------
        menu = Menu(
        courses=[
            Dish(
                course_type="starter",
                dish_name="Artichoke Textures with Citrus Foam",
                ingredients=[
                    Ingredient("artichoke", "main"),
                    Ingredient("lemon", "aroma"),
                    Ingredient("olive oil", "fat")
                ],
                techniques=["roasting", "emulsion", "foam"],
                cultural_influence=["Mediterranean"],
                presentation_notes="vertical plating with foam on top"
            ),
            Dish(
                course_type="main",
                dish_name="Miso-Glazed Sea Bass with Fermented Barley",
                ingredients=[
                    Ingredient("sea bass", "main"),
                    Ingredient("miso", "seasoning"),
                    Ingredient("barley", "base")
                ],
                techniques=["glazing", "fermentation", "slow-cook"],
                cultural_influence=["Japanese"],
                presentation_notes="Nordic minimal plating"
            ),
            Dish(
                course_type="dessert",
                dish_name="Citrus Almond Cream",
                ingredients=[
                    Ingredient("citrus blend", "main"),
                    Ingredient("almond", "fat"),
                    Ingredient("herbs", "aroma")
                ],
                techniques=["infusion", "whipping"],
                cultural_influence=["Fusion"],
                presentation_notes="creamy mousse with crunchy top layer"
            )
        ]
    )
,

        # ----------------------
        # JUSTIFICATION
        # ----------------------
        justification=Justification(
            why_this_menu=[
                "Uses seasonal winter ingredients like artichoke and citrus",
                "Matches client preferences for Mediterranean/Japanese fusion",
                "Formal event requires elegant minimal plating",
                "Gluten-free constraints addressed (tamari instead of soy sauce)"
            ],
            causal_links=[
                CausalLink(
                    cause="winter season",
                    effect="use of warm slow-cooked dishes"
                ),
                CausalLink(
                    cause="client adventurous profile",
                    effect="inclusion of molecular techniques"
                )
            ],
            major_adaptations=[
                "Replaced soy sauce with gluten-free tamari",
                "Blanched artichokes to remove bitterness"
            ]
        ),

        # ----------------------
        # OUTCOME
        # ----------------------
        outcome=Outcome(
            client_satisfaction=4.7,
            guest_comments=[
                "Memorable dessert",
                "Great balance of citrus flavors"
            ],
            success_metrics={
                "budget_compliance": True,
                "ingredient_availability": True,
                "timeliness": True
            },
            adaptation_difficulties=[
                "Needed almond substitution for allergic guest"
            ]
        )
    )


# ============================================================
# If run directly, print the example case
# ============================================================

if __name__ == "__main__":
    import json
    from dataclasses import asdict

    case = example_case()
    print(json.dumps(asdict(case), indent=4, ensure_ascii=False))
