from pathlib import Path
from owlready2 import (
    get_ontology,
    Thing,
    ObjectProperty,
    DataProperty,
    FunctionalProperty,
)

BASE_IRI = "http://example.org/menu-ontology#"


def export_ontology(output_path: str = "ontology.owl"):
    onto = get_ontology(BASE_IRI)

    with onto:
        # =========================
        # Classes
        # =========================
        class Ingredient(Thing): pass
        class Dish(Thing): pass
        class Menu(Thing): pass
        class Query(Thing): pass
        class Case(Thing): pass
        class Response(Thing): pass

        class Technique(Thing): pass
        class Cuisine(Thing): pass
        class Taste(Thing): pass
        class DietaryTag(Thing): pass
        class HealthFlag(Thing): pass
        class SensoryGoal(Thing): pass

        # =========================
        # Object properties
        # (No domain/range -> avoids duplicate edges in graphs)
        # =========================
        # Dish composition
        class hasIngredient(ObjectProperty): pass
        class usesTechnique(ObjectProperty): pass
        class hasCuisine(ObjectProperty): pass
        class hasTaste(ObjectProperty): pass
        class hasDietaryTag(ObjectProperty): pass
        class hasHealthFlag(ObjectProperty): pass

        # Menu composition
        class hasFirstCourse(ObjectProperty): pass
        class hasMainCourse(ObjectProperty): pass
        class hasDessert(ObjectProperty): pass

        # Case composition (THIS is what you want visually)
        class hasProblem(ObjectProperty): pass
        class hasSolution(ObjectProperty): pass
        class hasResponse(ObjectProperty): pass

        # Query links (optional)
        class hasSensoryGoal(ObjectProperty): pass

        # =========================
        # Data properties
        # =========================
        # Ingredient
        class ingredientName(DataProperty, FunctionalProperty):
            range = [str]

        class ingredientRole(DataProperty):
            range = [str]

        # Dish fields (single-valued)
        class dishName(DataProperty, FunctionalProperty):
            range = [str]

        class description(DataProperty):
            range = [str]

        class mainIngredient(DataProperty):
            range = [str]

        class courseType(DataProperty):
            range = [str]

        class primaryTaste(DataProperty):
            range = [str]

        class secondaryTaste(DataProperty):
            range = [str]

        class prepTime(DataProperty):
            range = [int]

        class cookTime(DataProperty):
            range = [int]

        class cookSpeed(DataProperty):
            range = [str]

        class difficulty(DataProperty):
            range = [str]

        class healthinessScore(DataProperty):
            range = [int]

        class healthLevel(DataProperty):
            range = [str]

        class justification(DataProperty):
            range = [str]

        # Query fields (single-valued)
        class eventType(DataProperty):
            range = [str]

        class season(DataProperty):
            range = [str]

        class numberOfGuests(DataProperty):
            range = [int]

        class presentationStyle(DataProperty):
            range = [str]

        class queryDescription(DataProperty):
            range = [str]

        # Case
        class caseId(DataProperty, FunctionalProperty):
            range = [int]

        # Response (rating ONLY here)
        class responseRating(DataProperty, FunctionalProperty):
            range = [int]

        class feedback(DataProperty):
            range = [str]

        # =========================
        # Restrictions (drive the "composed of" arrows)
        # =========================

        # Ingredient must have a name
        Ingredient.is_a.append(ingredientName.exactly(1, str))

        # Dish: required core fields
        Dish.is_a.append(dishName.exactly(1, str))
        Dish.is_a.append(description.exactly(1, str))
        Dish.is_a.append(mainIngredient.exactly(1, str))
        Dish.is_a.append(courseType.exactly(1, str))
        Dish.is_a.append(primaryTaste.exactly(1, str))
        Dish.is_a.append(secondaryTaste.exactly(1, str))
        Dish.is_a.append(prepTime.exactly(1, int))
        Dish.is_a.append(cookTime.exactly(1, int))
        Dish.is_a.append(cookSpeed.exactly(1, str))
        Dish.is_a.append(difficulty.exactly(1, str))
        Dish.is_a.append(healthinessScore.exactly(1, int))

        # Dish linked to the other classes (shows edges in graph)
        Dish.is_a.append(hasIngredient.some(Ingredient))
        Dish.is_a.append(usesTechnique.some(Technique))
        Dish.is_a.append(hasCuisine.some(Cuisine))
        Dish.is_a.append(hasTaste.some(Taste))
        Dish.is_a.append(hasDietaryTag.some(DietaryTag))
        Dish.is_a.append(hasHealthFlag.some(HealthFlag))

        # Menu composed of exactly 1 Dish each
        Menu.is_a.append(hasFirstCourse.exactly(1, Dish))
        Menu.is_a.append(hasMainCourse.exactly(1, Dish))
        Menu.is_a.append(hasDessert.exactly(1, Dish))

        # Query required core fields
        Query.is_a.append(eventType.exactly(1, str))
        Query.is_a.append(season.exactly(1, str))
        Query.is_a.append(numberOfGuests.exactly(1, int))
        Query.is_a.append(presentationStyle.exactly(1, str))
        Query.is_a.append(queryDescription.exactly(1, str))

        # Optional link: Query -> SensoryGoal (so SensoryGoal isn't floating)
        Query.is_a.append(hasSensoryGoal.some(SensoryGoal))

        # Response required core fields
        Response.is_a.append(responseRating.exactly(1, int))
        Response.is_a.append(feedback.exactly(1, str))

        # ✅ Case composed of Query + Menu + Response (like your picture)
        Case.is_a.append(caseId.exactly(1, int))
        Case.is_a.append(hasProblem.exactly(1, Query))
        Case.is_a.append(hasSolution.exactly(1, Menu))
        Case.is_a.append(hasResponse.exactly(1, Response))

    out = Path(output_path).resolve()
    onto.save(file=str(out), format="rdfxml")
    print(f"Saved OWL to: {out}")


if __name__ == "__main__":
    export_ontology("ontology.owl")
