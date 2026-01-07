'''
The main web application logic. Uses backend functions.
'''

from flask import Flask, render_template, request, redirect, url_for, session, abort
from program import run_recommender
import random
from image_scraper import get_webdriver, fetch_one_image_src, persist_image
from objectclasses import Dish, Ingredient, Query
from typing import List, Dict
import dataloader
from fourR import Retriever, Reuser, Reviser
import json
from dataloader import save_cases_to_json
from objectclasses import Query

# Flask application setup
app = Flask(__name__)
app.secret_key = "yufeng_raul_SBC"

# recommends menus based on user input using backend functions
@app.route("/recommend", methods=["POST"])
def recommend():
    # Collect user data from form
    data = {
            "event_type": request.form.get("event_type"),
            "season": request.form.get("season"),
            "number_of_guests": request.form.get("number_of_guests"),
            "description": request.form.get("description"),
            "dietary_group": request.form.get("dietary"),
            "preferred_techniques": request.form.getlist("preferred_techniques"),
            "presentation_style": request.form.get("presentation_style"),
            "sensory_goals": request.form.getlist("sensory_goals"),
            "culinary_traditions": request.form.getlist("culinary_traditions"),            
            "forbidden_ingredients": request.form.getlist("forbidden_ingredients"),
            "prep_time": request.form.get("prep_time"),
            "healthiness_level": request.form.get("healthiness_level")
            }

    # Store user data in session
    session["user_data"] = data
    print(data)
    # Generate menus and store them
    menus, all_justifications = run_recommender(data)

    # Attach justifications to each menu (aligned by menu index)
    for i, m in enumerate(menus):
        m["dish_justifications"] = all_justifications[i] if i < len(all_justifications) else [""] * len(m.get("dishes", []))

    print("\n === GENERATED MENUS ===")
    print(menus)
    session["menus_raw"] = menus  # store before images

    # Redirect to loading page
    return redirect(url_for("recommend_loading"))

# Recommendation view page
@app.route("/recommend/view", methods=["GET"])
def recommend_view():
    # Retrieve menus and user data from session
    menus = session.get("menus")
    if not menus: # if no menus, redirect to input form
        return redirect(url_for("input_form"))
    user_data = session.get("user_data", {})
    # Render recommendation page
    return render_template("recommend.html", menus=menus, user_data=user_data)

# Loading page while images are fetched via image scraper
@app.route("/recommend/loading", methods=["GET"])
def recommend_loading():
    # for debug purposes
    debug_data = session.get("user_data") or session.get("debug_user_data")
    # once loading is done, redirect to view page
    return render_template("loading.html", debug_data=debug_data)

# Gets descriptions of dishes from JSON database
def build_description_lookup(json_path: str) -> dict[str, str]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        values = data.values()
    else:
        values = data

    lookup = {}
    for d in values:
        if isinstance(d, dict):
            name = d.get("name") or d.get("title")
            desc = d.get("description") or d.get("desc") or ""
            if name:
                lookup[name] = desc
    return lookup

# Cleans dish name by removing special characters
def clean_name(s: str) -> str:
    return s.replace("*", "").strip()

# Recommendation result page with images and descriptions
@app.route("/recommend/result", methods=["GET"])
def recommend_result():
    # Retrieve raw menus from session
    menus = session.get("menus_raw")
    if not menus: # if no menus, redirect to input form
        return redirect(url_for("input_form"))

    # Collect unique dishes shown
    dish_set = set()
    for m in menus:
        dish_set.update(m.get("dishes", []))

    # Use only ONE webdriver for all dish queries
    wd = get_webdriver()
    try:
        dish_to_img = {}
        for dish in dish_set:
            src = fetch_one_image_src(dish, wd=wd) # fetch image src
            if src:
                saved_name = persist_image("static/dish_images", dish, src)
                dish_to_img[dish] = saved_name 
            else:
                dish_to_img[dish] = None
    finally:
        wd.quit()

    # Attach per-menu mapping
    for m in menus:
        m["dish_images"] = {dish: dish_to_img.get(dish) for dish in m.get("dishes", [])}

    # Get descriptions from JSON database (base dishes)
    desc_by_name = build_description_lookup("data/dish_database_5k.json")

    for m in menus:
        dishes = m.get("dishes", [])
        # Attach descriptions aligned with dishes
        m["dish_descriptions"] = []
        for dish_name in dishes:
            key = clean_name(dish_name)  # removes "*"
            m["dish_descriptions"].append(desc_by_name.get(key, ""))
        # make sure justifications list matches dishes list
        if "dish_justifications" not in m or not isinstance(m["dish_justifications"], list):
            m["dish_justifications"] = [""] * len(dishes)
        else:
            justs = m["dish_justifications"]
            if len(justs) < len(dishes):
                m["dish_justifications"] = justs + [""] * (len(dishes) - len(justs))
            elif len(justs) > len(dishes):
                m["dish_justifications"] = justs[:len(dishes)]

    session["menus"] = menus
    user_data = session.get("user_data", {})
    # Render recommendation page
    return render_template("recommend.html", menus=menus, user_data=user_data)

# Auxiliary class to convert form data to Query object
class DishStub:
    def __init__(self, name: str):
        self.name = name

# Auxiliary class to simulate proposal object for saving cases
class ProposalStub:
    def __init__(self, first, main, dessert):
        self.first_course = DishStub(first)
        self.main_course = DishStub(main)
        self.dessert = DishStub(dessert)

# feedback collection page
@app.route("/feedback/<int:menu_index>", methods=["GET", "POST"])
def feedback(menu_index):
    menus = session.get("menus")
    query = session.get("user_data")
    # error handling
    if not menus or menu_index < 0 or menu_index >= len(menus):
        abort(404)
    selected_menu = menus[menu_index]
    # handle feedback submission
    if request.method == "POST":
        rating = int(request.form.get("rating"))
        comments = request.form.get("comments")

        response = {
            "rating": rating,
            "feedback": comments
        }

        dishes = selected_menu.get("dishes", [])

        proposal = ProposalStub(
            first=dishes[0] if len(dishes) > 0 else None,
            main=dishes[1] if len(dishes) > 1 else None,
            dessert=dishes[2] if len(dishes) > 2 else None,
        )
        # Save the case with feedback
        save_cases_to_json(
            query=query,
            proposal=proposal,
            response=response,
            json_file_path="data/dynamic_case_database.json",
            verbose=True
        )
        # Redirect to input form after submission
        return redirect(url_for("input_form"))
    # Render feedback form
    return render_template("feedback.html", menu=selected_menu, menu_index=menu_index)

# Information collection page
@app.route("/", methods=["GET", "POST"])
def input_form():
    saved = False
    # handle form submission
    if request.method == "POST":
        data = {
            "event_type": request.form.get("event_type"),
            "season": request.form.get("season"),
            "number_of_guests": request.form.get("number_of_guests"),
            "description": request.form.get("description"),
            "dietary_group": request.form.get("dietary"),
            "preferred_techniques": request.form.getlist("preferred_techniques"),
            "presentation_style": request.form.get("presentation_style"),
            "sensory_goals": request.form.getlist("sensory_goals"),
            "culinary_traditions": request.form.getlist("culinary_traditions"),            
            "forbidden_ingredients": request.form.getlist("forbidden_ingredients"),
            "prep_time": request.form.get("prep_time"),
            "healthiness_level": request.form.get("healthiness_level")
            }
        # Store user data in session
        session["debug_user_data"] = data  
        saved = True
    # Render input form
    return render_template("index.html", saved=saved)

# main loop
if __name__ == "__main__":
    app.run(debug=False)
