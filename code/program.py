from objectclasses import Dish, Ingredient
from typing import List, Dict
import dataloader
from fourR import Retriever, Reuser, Reviser

if __name__ == "__main__":

    dishes, cuisines = dataloader.load_dishes_from_json('data/dish_database_5k.json')
    cases = dataloader.load_cases_from_json('data/case_database.json', dishes)
    ingredient_category, ingredient_replacement = dataloader.load_ingredient_info('data/ingredient_category.json', 'data/ingredient_replacement.json')

    query = cases[1].problem

    retriever = Retriever(cases)
    reuser = Reuser(query, dishes, ingredient_category, ingredient_replacement)
    reviser = Reviser(reuser)
    
    topn = retriever.retrieve_top(query, top_n=4)
    
    proposal = reuser.reuse([(cases[x], y) for x, y in topn], rejects=None)
    proposal = reviser.revise(proposal, query, [(cases[x], y) for x, y in topn], rejects=None)

    print("Proposed Menu:")
    print(proposal)

    #dataloader.save_cases_to_json(cases, 'data/case_database2.json', verbose=True)
