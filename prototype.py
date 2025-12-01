import json
import random

# ============================================================
#                        1. RETRIEVE
# ============================================================

class Retriever:
    def __init__(self, case_base):
        self.case_base = case_base

        # Weight configuration
        self.weights = {
            "Tipo": 0.30,
            "Estacion": 0.20,
            "Diet": 0.30,
            "Pax": 0.10,
            "Forbidden": 0.10
        }

    def similarity(self, case1, case2):
        score = 0.0
        w = self.weights

        if case1["Tipo_de_Evento"] == case2["Tipo_de_Evento"]:
            score += w["Tipo"]
        if case1["Estación_Evento"] == case2["Estación_Evento"]:
            score += w["Estacion"]
        if case1["Grupo_Dietario"] == case2["Grupo_Dietario"]:
            score += w["Diet"]

        diff = abs(case1["Número_comensales"] - case2["Número_comensales"])
        pax_sim = max(0, 1 - diff / 500)
        score += pax_sim * w["Pax"]

        s1 = set(case1["Ingredientes_prohibidos"])
        s2 = set(case2["Ingredientes_prohibidos"])
        union = len(s1 | s2)
        inter = len(s1 & s2)
        ing_sim = inter / union if union > 0 else 1
        score += ing_sim * w["Forbidden"]

        return score

    def retrieve_top(self, new_case, top_n=3):
        scored = []

        print("\n[RETRIEVE] Computing similarities...")
        for case in self.case_base:
            score = self.similarity(new_case, case["problem"])
            print(f"   - Case {case['id']} -> Score: {score:.4f}")
            scored.append((case, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        scored = scored[:top_n]

        total = sum(s for _, s in scored)
        normalized = [(c, s / total if total > 0 else 1/len(scored)) for c, s in scored]

        print(f"[RETRIEVE] Retrieved top {top_n} cases.")
        return normalized


# ============================================================
#                        2. REUSE
# ============================================================

class Reuser:
    def reuse_w(self, retrieved_cases, rejects=None):
        print("[REUSE] Creating possible solution.")

        new_case = {"Platos": {
            "Primero": {"Nombre": ""},
            "Segundo": {"Nombre": ""},
            "Postre": {"Nombre": ""}
        }}

        for course in new_case["Platos"].keys():

            adjusted_cases = []

            for case, weight in retrieved_cases:
                dish_name = case["solution"]["Platos"][course]["Nombre"]
                penalty = 1.0

                # ----------------------------------------
                # APPLY USER FEEDBACK / REJECTION REASON
                # ----------------------------------------
                if rejects:
                    for rejected_solution, reason in rejects:
                        reason = reason.lower()

                        # ❌ User rejected this specific course
                        if reason == course.lower():
                            bad_dish = rejected_solution["Platos"][course]["Nombre"]
                            if dish_name == bad_dish:
                                penalty = 0  # hard reject this dish
                        
                        # ⚠️ User disliked something else, but not this course
                        elif reason in ("primero", "segundo", "postre"):
                            # No penalty for this course
                            continue

                        # ⚠️ "otros" → dislike whole menu → apply soft global penalty
                        elif reason == "otros":
                            penalty *= 0.5

                if penalty > 0:
                    adjusted_cases.append((case, weight * penalty))

            if not adjusted_cases:
                print(f"[REUSE] No valid cases for course '{course}' after rejection filtering.")
                return None

            # ----------------------------------------
            # SAMPLE DISH BASED ON ADJUSTED WEIGHTS
            # ----------------------------------------
            dishes = [c["solution"]["Platos"][course]["Nombre"] for c, _ in adjusted_cases]
            weights = [w for _, w in adjusted_cases]

            total = sum(weights)
            weights = [w / total for w in weights]

            selected = random.choices(dishes, weights=weights, k=1)[0]
            new_case["Platos"][course]["Nombre"] = selected

        return new_case


# ============================================================
#                        3. REVISE
# ============================================================

class Reviser:
    def __init__(self, reuser):
        self.reuser = reuser

    def revise(self, proposed_solution, query, alternatives, rejects=None):

        if proposed_solution is None:
            print("[REVISE] No further solutions possible.")
            return None

        print("\n[REVISE] Proposed Menu:")
        print(json.dumps(proposed_solution, indent=2, ensure_ascii=False))

        feedback = input("Do you accept this menu? ([Y]/n): ").strip().lower()

        if feedback == 'n':
            print("[REVISE] Solution rejected.")
            feedback = input("What was wrong with the menu? (Primero, Segundo, Postre, Otros): ").strip().lower()
            rejects = rejects + [(proposed_solution, feedback)] if rejects else [(proposed_solution, feedback)]
            new_solution = self.reuser.weighted_reuse(alternatives, rejects)
            return self.revise(new_solution, query, alternatives, rejects)

        print("[REVISE] Accepted final solution.")
        return proposed_solution


# ============================================================
#                        4. RETAIN
# ============================================================

class Retainer:
    def __init__(self, case_base):
        self.case_base = case_base

    def retain(self, problem, solution):
        new_id = len(self.case_base) + 1
        new_case = {
            "id": new_id,
            "problem": problem,
            "solution": solution
        }
        self.case_base.append(new_case)
        print(f"[RETAIN] Stored new case ID {new_id}.")
        return new_case


# ============================================================
#                      MAIN CBR SYSTEM
# ============================================================

class MenuCBR:
    def __init__(self):
        self.case_base = []
        self._load_toy_data()

        self.retriever = Retriever(self.case_base)
        self.reuser = Reuser()
        self.reviser = Reviser(self.reuser)
        self.retain_module = Retainer(self.case_base)

    def _load_toy_data(self):
        case_1 = {
            "id": 1,
            "problem": {
                "Tipo_de_Evento": "Boda",
                "Estación_Evento": "Verano",
                "Número_comensales": 80,
                "Grupo_Dietario": "Omnívoro",
                "Ingredientes_prohibidos": ["Mariscos"]
            },
            "solution": {
                "Platos": {
                    "Primero": {"Nombre": "Ensalada de quinoa"},
                    "Segundo": {"Nombre": "Filete de ternera"},
                    "Postre": {"Nombre": "Tarta de frutas"}
                }
            }
        }

        case_2 = {
            "id": 2,
            "problem": {
                "Tipo_de_Evento": "Corporativo",
                "Estación_Evento": "Invierno",
                "Número_comensales": 200,
                "Grupo_Dietario": "Vegetariano",
                "Ingredientes_prohibidos": ["Nueces"]
            },
            "solution": {
                "Platos": {
                    "Primero": {"Nombre": "Crema de calabaza"},
                    "Segundo": {"Nombre": "Lasaña de espinacas"},
                    "Postre": {"Nombre": "Brownie vegano"}
                }
            }
        }

        case_3 = {
            "id": 3,
            "problem": {
                "Tipo_de_Evento": "Cumpleaños",
                "Estación_Evento": "Primavera",
                "Número_comensales": 20,
                "Grupo_Dietario": "Omnívoro",
                "Ingredientes_prohibidos": ["Picante"]
            },
            "solution": {
                "Platos": {
                    "Primero": {"Nombre": "Palitos de mozzarella"},
                    "Segundo": {"Nombre": "Mini hamburguesas"},
                    "Postre": {"Nombre": "Helado de vainilla"}
                }
            }
        }

        self.case_base.extend([case_1, case_2, case_3])

    def solve(self, query):
        print(f"\n======== NEW QUERY: {query['Tipo_de_Evento']} / {query['Grupo_Dietario']} ========")

        retrieved_cases = self.retriever.retrieve_top(query, top_n=3)
        candidate = self.reuser.reuse_w(retrieved_cases, rejects=None)
        revised = self.reviser.revise(candidate, query, retrieved_cases)

        if revised is not None:
            self.retain_module.retain(query, revised)

        return revised


# ============================================================
#                     EXECUTION EXAMPLE
# ============================================================

cbr = MenuCBR()

query = {
    "Tipo_de_Evento": "Boda",
    "Estación_Evento": "Verano",
    "Número_comensales": 60,
    "Grupo_Dietario": "Omnívoro",
    "Ingredientes_prohibidos": ["Mariscos"]
}

result = cbr.solve(query)

print("\n--- FINAL RECOMMENDED MENU ---")
print(json.dumps(result, indent=2, ensure_ascii=False))
print(f"\n--- CASES IN MEMORY: {len(cbr.case_base)} ---")
