'''
This program runs a test build of the backend.

It runs on the terminal, and will automatically fetch a case from the database without asking for user input.
It is meant for testing purposes.
'''

from objectclasses import Dish, Ingredient, Query
from typing import List, Dict
import dataloader
from fourR import Retriever, Reuser, Reviser
from input_system import ask_query, ask_response

# Converts a dictionary to a Query object
def dict_to_query(data: dict) -> Query:
    return Query(
        event_type=data.get("event_type"),
        season=data.get("season"),
        number_of_guests=int(data.get("number_of_guests", 0)),
        techniques=data.get("preferred_techniques", []),
        presentation_style=data.get("presentation_style"),
        sensory_goals=data.get("sensory_goals", []),
        description=data.get("description"),
        culinary_traditions=data.get("culinary_traditions", []),
        dietary_group=data.get("dietary_group", []),
        forbidden_ingredients=data.get("forbidden_ingredients", []),
        prep_time=int(data.get("prep_time", 0)) if data.get("prep_time") else None,
        healthiness_level=data.get("healthiness_level"),
    )

# Function to run the recommender system
def run_recommender(user_data: dict):
    dishes, cuisines = dataloader.load_dishes_from_json('data/dish_database_5k.json')
    cases = dataloader.load_cases_from_json('data/dynamic_case_database.json', dishes)
    ingredient_category, ingredient_replacement = dataloader.load_ingredient_info(
        'data/ingredient_category.json',
        'data/ingredient_replacement.json'
    )
    query = dict_to_query(user_data)

    retriever = Retriever(cases, use_llm=True)
    reuser = Reuser(query, dishes, ingredient_category, ingredient_replacement)
    reviser = Reviser(reuser) # in the web version, we do not use the reviser for now

    topn = retriever.retrieve_top(query, top_n=4)

    # we generate 3 proposals, avoinding the previous ones
    proposal1 = reuser.reuse([(cases[x], y) for x, y in topn], rejects=None)
    proposal2 = reuser.reuse(
        [(cases[x], y) for x, y in topn],
        rejects=[[proposal1, "avoid"]])
    proposal3 = reuser.reuse(
        [(cases[x], y) for x, y in topn],
        rejects=[[proposal1, "avoid"], [proposal2, "avoid"]])
    proposals = [proposal1, proposal2, proposal3]

    # collect justifications
    all_justifications = [
        [
            getattr(p.first_course, "justification", "") or "",
            getattr(p.main_course, "justification", "") or "",
            getattr(p.dessert, "justification", "") or "",
        ]
        for p in proposals
    ]
    # return in a format suitable for the web app
    return [
        {
            "title": "Menu 1",
            "dishes": [str(proposal1.first_course.name), str(proposal1.main_course.name), str(proposal1.dessert.name)]
        },
        {
            "title": "Menu 2",
            "dishes": [str(proposal2.first_course.name), str(proposal2.main_course.name), str(proposal2.dessert.name)]
        },
        {
            "title": "Menu 3",
            "dishes": [str(proposal3.first_course.name), str(proposal3.main_course.name), str(proposal3.dessert.name)]
        }
    ], all_justifications

    # proposal = reviser.revise(proposal, query, [(cases[x], y) for x, y in topn], rejects=None)
    # later: return recommendations
    #return proposal

# Run the program on the terminal
if __name__ == "__main__":
    # loading data
    dishes, cuisines = dataloader.load_dishes_from_json('data/dish_database_5k.json')
    cases = dataloader.load_cases_from_json('data/dynamic_case_database.json', dishes)
    ingredient_category, ingredient_replacement = dataloader.load_ingredient_info('data/ingredient_category.json', 'data/ingredient_replacement.json')
    # Initialize query from user input
    query = dict_to_query(ask_query(saved=False))
    retriever = Retriever(cases)
    reuser = Reuser(query, dishes, ingredient_category, ingredient_replacement)
    reviser = Reviser(reuser)
    # retrieve top 4 cases
    topn = retriever.retrieve_top(query, top_n=4)
    # we generate 3 proposals, avoinding the previous ones
    proposal1 = reuser.reuse([(cases[x], y) for x, y in topn], rejects=None)
    proposal2 = reuser.reuse([(cases[x], y) for x, y in topn], rejects=[[proposal1, "avoid"]])
    proposal3 = reuser.reuse([(cases[x], y) for x, y in topn], rejects=[[proposal1, "avoid"],
                                                                        [proposal2, "avoid"]])
    # Format and print proposed menus
    print("\n=== Proposed Menus ===")

    menus = [
        ("Menu 1", proposal1),
        ("Menu 2", proposal2),
        ("Menu 3", proposal3),]

    for title, proposal in menus:
        print(f"\n{title}:")
        print(f"  • Starter : {proposal.first_course.name}")
        print(f"  • Main    : {proposal.main_course.name}")
        print(f"  • Dessert : {proposal.dessert.name}")

    # Let user choose 1 of the 3 menus
    chosen_menu = int(input("\nSelect the menu you like the most (1-3): "))
    while chosen_menu not in [1, 2, 3]:
        chosen_menu = int(input("Please select a valid menu (1-3): "))
    final_proposal = menus[chosen_menu - 1][1]

    proposal = reviser.revise(final_proposal, query, [(cases[x], y) for x, y in topn], rejects=None)

    proposals = [proposal1, proposal2, proposal3]

    print("\n=== Justifications ===")
    print("First Course: ", getattr(proposal.first_course, "justification", "") or "No justification provided.")
    print("Main Course: ", getattr(proposal.main_course, "justification", "") or "No justification provided.")
    print("Dessert: ", getattr(proposal.dessert, "justification", "") or "No justification provided.")
    # Ask for feedback
    print("\n Feedback Revised Menu: tell us what you think about this menu!")
    response = ask_response()

    dataloader.save_cases_to_json(query, proposal, response, 'data/dynamic_case_database.json', verbose=True)
