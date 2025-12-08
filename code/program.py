from objectclasses import Dish, Ingredient
from typing import List, Dict
import dataloader
from fourR import Retriever, Reuser, Reviser

if __name__ == "__main__":

    dishes, cuisines = dataloader.load_dishes_from_json('code/data/dish_database_5k.json')
    cases = dataloader.load_cases_from_json('code/data/case_database.json', dishes)

    query = cases[1].problem

    retriever = Retriever(cases)
    reuser = Reuser(query, dishes)
    reviser = Reviser(reuser)
    
    topn = retriever.retrieve_top(query, top_n=4)
    
    proposal = reuser.reuse([(cases[x], y) for x, y in topn], rejects=None)
    proposal = reviser.revise(proposal, query, [(cases[x], y) for x, y in topn], rejects=None)

    print("Proposed Menu:")
    print(proposal)

    dataloader.save_cases_to_json(cases, 'code/data/case_database2.json', verbose=True)
