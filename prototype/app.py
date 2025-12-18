from flask import Flask, render_template, request, redirect, url_for, session, abort
import random

# --- your scraper functions ---
# Make sure image_scraper.py contains:
# - get_webdriver()
# - fetch_one_image_url(query, wd)
# - persist_image(folder_path, file_name, url_or_data_src)   (should handle base64 too, see my earlier version)
#
# If your persist_image currently only supports http(s), update it to handle data:image;base64.
from image_scraper import get_webdriver, fetch_one_image_src, persist_image

# ----- placeholder dishes for menus -----
DISHES = [
    "Grilled Vegetable Skewers with Herb Quinoa",
    "Creamy Pumpkin Soup with Toasted Seeds",
    "Tofu Stir-Fry with Seasonal Vegetables",
    "Seared Salmon with Lemon Dill Sauce",
    "Roast Chicken with Garlic Mashed Potatoes",
    "Mushroom Risotto with Truffle Oil",
    "Chickpea and Spinach Curry with Basmati Rice",
    "Pasta Primavera with Fresh Basil",
    "Chocolate Lava Cake with Vanilla Ice Cream",
    "Seasonal Fruit Tart with Almond Cream",
]

def generate_three_menus():
    """Return 3 placeholder menus with minimal overlap."""
    menus = []
    used = set()
    for i in range(3):
        remaining = [d for d in DISHES if d not in used]
        if len(remaining) < 3:
            dishes = random.sample(DISHES, 3)
        else:
            dishes = random.sample(remaining, 3)
            used.update(dishes)

        menus.append({"title": f"Menu {i+1}", "dishes": dishes})
    return menus


# ---- NEW: loading route (so user sees “please wait” immediately) ----
app = Flask(__name__)
app.secret_key = "yufeng_raul_SBC"

@app.route("/recommend", methods=["POST"])
def recommend():
    # Save user data immediately
    data = {
        "event_type": request.form.get("event_type"),
        "num_guests": request.form.get("num_guests"),
        "event_date": request.form.get("event_date"),
        "event_notes": request.form.get("event_notes"),
        "dietary": request.form.getlist("dietary"),
        "allergies": request.form.get("allergies"),
        "dislikes": request.form.get("dislikes"),
        "preferred_cuisines": request.form.getlist("preferred_cuisines"),
        "preferred_techniques": request.form.getlist("preferred_techniques"),
        "preferred_flavours": request.form.getlist("preferred_flavours"),
    }
    session["user_data"] = data

    # Generate menus and store them
    menus = generate_three_menus(data)
    session["menus_raw"] = menus  # store before images

    # Redirect to a loading page that will trigger actual work
    return redirect(url_for("recommend_loading"))


@app.route("/recommend/loading", methods=["GET"])
def recommend_loading():
    """
    Shows a loading page that auto-requests /recommend/result.
    This way the user sees feedback immediately.
    """
    return render_template("loading.html")


@app.route("/recommend/result", methods=["GET"])
def recommend_result():
    """
    Does the scraping work (still synchronous), but user already saw loading UI.
    """
    menus = session.get("menus_raw")
    if not menus:
        return redirect(url_for("input_form"))

    # Collect unique dishes shown
    dish_set = set()
    for m in menus:
        dish_set.update(m["dishes"])

    # Use ONE webdriver for all dish queries (much faster)
    wd = get_webdriver()
    try:
        dish_to_img = {}
        for dish in dish_set:
            src = fetch_one_image_src(dish, wd=wd)  # may return data:image... or http(s)
            if src:
                # Save into Flask static folder so it can be served
                saved_name = persist_image("static/dish_images", dish, src)
                # persist_image should return filename (recommended). If yours doesn't, set saved_name=None.
                dish_to_img[dish] = saved_name
            else:
                dish_to_img[dish] = None
    finally:
        wd.quit()

    # Attach per-menu mapping
    for m in menus:
        m["dish_images"] = {dish: dish_to_img.get(dish) for dish in m["dishes"]}

    # Store final menus (with images) for feedback route
    session["menus"] = menus

    user_data = session.get("user_data", {})
    return render_template("recommend.html", menus=menus, user_data=user_data)


@app.route("/feedback/<int:menu_index>", methods=["GET", "POST"])
def feedback(menu_index):
    menus = session.get("menus")
    if not menus or menu_index < 0 or menu_index >= len(menus):
        abort(404)

    selected_menu = menus[menu_index]
    user_data = session.get("user_data", {})

    if request.method == "POST":
        rating = request.form.get("rating")
        comments = request.form.get("comments")

        feedback_data = {
            "menu_index": menu_index,
            "selected_menu": selected_menu,
            "rating": rating,
            "comments": comments,
            "user_data": user_data,
        }

        print("=== FEEDBACK RECEIVED ===")
        print(feedback_data)

        return redirect(url_for("input_form"))

    return render_template("feedback.html", menu=selected_menu, menu_index=menu_index)


@app.route("/", methods=["GET", "POST"])
def input_form():
    saved = False

    if request.method == "POST":
        data = {
            "event_type": request.form.get("event_type"),
            "num_guests": request.form.get("num_guests"),
            "event_date": request.form.get("event_date"),
            "event_notes": request.form.get("event_notes"),
            "dietary": request.form.getlist("dietary"),
            "allergies": request.form.get("allergies"),
            "dislikes": request.form.get("dislikes"),
            "preferred_cuisines": request.form.getlist("preferred_cuisines"),
            "preferred_techniques": request.form.getlist("preferred_techniques"),
            "preferred_flavours": request.form.getlist("preferred_flavours"),
        }
        print("=== USER INPUT RECEIVED ===")
        print(data)
        saved = True

    return render_template("index.html", saved=saved)


if __name__ == "__main__":
    app.run(debug=True)
