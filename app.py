from flask import Flask, render_template, request, redirect, url_for, session, abort
import random

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

        menus.append(
            {
                "title": f"Menu {i+1}",
                "dishes": dishes,
            }
        )
    return menus

app = Flask(__name__)
app.secret_key = "yufeng_raul_SBC"

@app.route("/recommend", methods=["POST"])
def recommend():
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

    menus = generate_three_menus()

    # NEW: keep data and menus so the feedback screen can use them
    session["user_data"] = data
    session["menus"] = menus

    return render_template("recommend.html", menus=menus, user_data=data)


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

        # after saving feedback, redirect back home (or to a "thank you" page)
        return redirect(url_for("input_form"))  # change to your index route name if different

    # GET: show the feedback form for this menu
    return render_template("feedback.html",
                           menu=selected_menu,
                           menu_index=menu_index)


@app.route("/", methods=["GET", "POST"])
def input_form():
    saved = False

    if request.method == "POST":
        # Collect all form fields (for future CBR use)
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
