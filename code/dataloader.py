'''
This script loads the data from and into their appropriate disk formats (JSON, CSV) and loads it onto their
appropriate datastructures (mainly dicts).
'''

from typing import Dict, List
from objectclasses import Dish, Case, Query, Menu
import json
import os

def load_dishes_from_json(json_file_path: str) -> tuple[dict[int, Case], dict[str, List[Dish]]]:
    """
    Load dishes from a JSON file and return a dictionary with dish names as keys.
    """
    with open(json_file_path, 'r', encoding='utf-8', errors='ignore') as file:
        dishes_data = json.load(file)
    
    dishes_dict = {}
    cuisines_dict = {}
    
    for dish_data in dishes_data:
        dish = Dish(**dish_data)
        dishes_dict[dish.name] = dish
        for cuisine in dish.cuisines:
            cuisines_dict.setdefault(cuisine, []).append(dish)
    
    return dishes_dict, cuisines_dict

def save_dishes_to_json(dishes: Dict[str, Dish], json_file_path: str):
    """
    Save dishes from a dictionary to a JSON file.
    """
    dishes_list = [dish.__dict__ for dish in dishes.values()]
    
    with open(json_file_path, 'w') as file:
        json.dump(dishes_list, file, indent=4)

def load_cases_from_json(json_file_path: str, dishes: Dict[str, Dish]) -> Dict[int, Case]:
    """
    Load cases from a JSON file and return a dictionary with case IDs as keys.
    """
    with open(json_file_path, 'r', encoding='utf-8', errors='ignore') as file:
        cases_data = json.load(file)
    
    cases_dict = {}
    
    for case_data in cases_data:
        # Extract 'problem' and 'solution' to create the respective objects
        problem_data = case_data.get("problem")
        solution_data = case_data.get("solution")
        
        # Assuming the `Query` and `Menu` classes have constructors that can handle this data
        problem = Query(**problem_data)
        
        solution = Menu(
            first_course=dishes[solution_data.get('first_course')],
            main_course=dishes[solution_data.get('main_course')],
            dessert=dishes[solution_data.get('dessert')]
        )
        
        # Create a Case object and add it to the dictionary
        case = Case(id=case_data['id'], problem=problem, solution=solution)
        cases_dict[case.id] = case
    
    return cases_dict

def load_ingredient_info(json_ingredient_category: str, json_ingredient_replacement: str):
    """
    Load cases from a JSON file and return a dictionary with case IDs as keys.
    """
    with open(json_ingredient_category, 'r', encoding='utf-8', errors='ignore') as file:
        ingredient_category = json.load(file)
    
    with open(json_ingredient_replacement, 'r', encoding='utf-8', errors='ignore') as file:
        ingredient_replacement = json.load(file)
    
    return ingredient_category, ingredient_replacement

def to_dict(obj):
    """
    Converts objects (dataclass or normal objects) to dict safely.
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)

def save_cases_to_json(query, proposal, response, json_file_path: str, verbose: bool = False):
    """
    Append ONE new case to the JSON case base.
    """
    
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                cases = json.load(f)
            if not isinstance(cases, list):
                cases = []
        except Exception:
            cases = []
    else:
        cases = []

    if cases:
        max_id = max(c.get("id", 0) for c in cases if isinstance(c, dict))
        new_id = max_id + 1
    else:
        new_id = 1

    sol = {
        "first_course": proposal.first_course.name,
        "main_course": proposal.main_course.name,
        "dessert": proposal.dessert.name,
    }

    case_dict = {
        "id": new_id,
        "problem": to_dict(query),
        "solution": sol,
        "response": to_dict(response),
    }

    cases.append(case_dict)
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=4, ensure_ascii=False)

    if verbose:
        print(f"Saved new case (id={new_id}) to {json_file_path}")