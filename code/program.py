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
    # For now just prove we received it
    dishes, cuisines = dataloader.load_dishes_from_json('data/dish_database_5k.json')
    cases = dataloader.load_cases_from_json('data/case_database.json', dishes)
    ingredient_category, ingredient_replacement = dataloader.load_ingredient_info('data/ingredient_category.json', 'data/ingredient_replacement.json')
    query = dict_to_query(user_data)
    print("QUERY TRANSFORMED:", query, flush=True)
    retriever = Retriever(cases)
    reuser = Reuser(query, dishes, ingredient_category, ingredient_replacement)
    reviser = Reviser(reuser)
    
    topn = retriever.retrieve_top(query, top_n=4)
    
    proposal = reuser.reuse([(cases[x], y) for x, y in topn], rejects=None)
    proposal = reviser.revise(proposal, query, [(cases[x], y) for x, y in topn], rejects=None)
    # later: return recommendations
    return proposal


if __name__ == "__main__":

    dishes, cuisines = dataloader.load_dishes_from_json('data/dish_database_5k.json')
    cases = dataloader.load_cases_from_json('data/case_database.json', dishes)
    ingredient_category, ingredient_replacement = dataloader.load_ingredient_info('data/ingredient_category.json', 'data/ingredient_replacement.json')

    query = cases[1].problem  
    print("Query:")
    print(query)
    retriever = Retriever(cases)
    reuser = Reuser(query, dishes, ingredient_category, ingredient_replacement)
    reviser = Reviser(reuser)
    
    topn = retriever.retrieve_top(query, top_n=4)
    
    proposal1 = reuser.reuse([(cases[x], y) for x, y in topn], rejects=None)
    proposal2 = reuser.reuse([(cases[x], y) for x, y in topn], rejects=[[proposal1, "others"]])
    proposal3 = reuser.reuse([(cases[x], y) for x, y in topn], rejects=[[proposal1, "others"],
                                                                        [proposal2, "others"]])

    proposal = reviser.revise(proposal1, query, [(cases[x], y) for x, y in topn], rejects=None)

    print("Proposed Menu:")
    print(proposal)

    #dataloader.save_cases_to_json(cases, 'data/case_database2.json', verbose=True)
