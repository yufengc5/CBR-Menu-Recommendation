'''
This program runs a test build of the backend.

It runs on the terminal, and will automatically fetch a case from the database without asking for user input.
It is meant for testing purposes.
'''

from objectclasses import Dish, Ingredient, Query
from typing import List, Dict
import dataloader
from fourR import Retriever, Reuser, Reviser

def dict_to_query(data: dict) -> Query:
    return Query(
        event_type=data.get("event_type"),
        season=data.get("season"),
        number_of_guests=int(data.get("number_of_guests", 0)),
        techniques=data.get("preferred_techniques", []),
        presentation_style=data.get("presentation_style"),
        sensory_goals=data.get("sensory_goals", []),
        description=data.get("description"),
        culinary_tradition=data.get("culinary_traditions", []),
        dietary_group=data.get("dietary_groups", []),
        forbidden_ingredients=data.get("forbidden_ingredients", []),
        prep_time=int(data.get("prep_time", 0)) if data.get("prep_time") else None,
        healthiness_level=data.get("healthiness_level"),
    )

# USAR COMO UNA API
def run_recommender(user_data: dict):
    dishes, cuisines = dataloader.load_dishes_from_json('data/dish_database_5k.json')
    cases = dataloader.load_cases_from_json('data/case_database.json', dishes)
    ingredient_category, ingredient_replacement = dataloader.load_ingredient_info(
        'data/ingredient_category.json',
        'data/ingredient_replacement.json'
    )

    query = dict_to_query(user_data)

    retriever = Retriever(cases)
    reuser = Reuser(query, dishes, ingredient_category, ingredient_replacement)
    reviser = Reviser(reuser)

    topn = retriever.retrieve_top(query, top_n=4)

    proposal1 = reuser.reuse([(cases[x], y) for x, y in topn], rejects=None)
    proposal2 = reuser.reuse(
        [(cases[x], y) for x, y in topn],
        rejects=[[proposal1, "avoid"]]
    )
    proposal3 = reuser.reuse(
        [(cases[x], y) for x, y in topn],
        rejects=[[proposal1, "avoid"], [proposal2, "avoid"]]
    )
    proposals = [proposal1, proposal2, proposal3]

    all_justifications = [
        [
            getattr(p.first_course, "justification", "") or "",
            getattr(p.main_course, "justification", "") or "",
            getattr(p.dessert, "justification", "") or "",
        ]
        for p in proposals
    ]

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


if __name__ == "__main__":

    dishes, cuisines = dataloader.load_dishes_from_json('data/dish_database_5k.json')
    cases = dataloader.load_cases_from_json('data/case_database.json', dishes)
    ingredient_category, ingredient_replacement = dataloader.load_ingredient_info('data/ingredient_category.json', 'data/ingredient_replacement.json')

    query = cases[2].problem  
    #print("Query:")
    #print(query)
    retriever = Retriever(cases)
    reuser = Reuser(query, dishes, ingredient_category, ingredient_replacement)
    reviser = Reviser(reuser)
    
    topn = retriever.retrieve_top(query, top_n=4)
    
    proposal1 = reuser.reuse([(cases[x], y) for x, y in topn], rejects=None)
    proposal2 = reuser.reuse([(cases[x], y) for x, y in topn], rejects=[[proposal1, "avoid"]])
    proposal3 = reuser.reuse([(cases[x], y) for x, y in topn], rejects=[[proposal1, "avoid"],
                                                                        [proposal2, "avoid"]])

    print("Proposed Menu 1:")
    print(proposal1)
    print("Proposed Menu 2:")
    print(proposal2)
    print("Proposed Menu 3:")
    print(proposal3)

    print([
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
    ])
    print("\n\n\n")
    print("JUSTIFICATION: " + proposal3.dessert.justification)
    #proposal = reviser.revise(proposal1, query, [(cases[x], y) for x, y in topn], rejects=None)

    #print("Proposed Menu:")
    #print(proposal)

    dataloader.save_cases_to_json(cases, 'data/case_database2.json', verbose=True)
