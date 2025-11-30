import json

# Partimos de la plantilla generada por ChatGPT, y vamos mejorando
# las cuatro fases del ciclo CBR (4R): Retrieve, Reuse, Revise, Retain.

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

    def similarity(self, input_prob, case_prob):
        """Computes a weighted similarity score between 0 and 1."""
        score = 0.0
        
        w = self.weights

        # Title, Season, Diet: exact match
        if input_prob["Tipo_de_Evento"] == case_prob["Tipo_de_Evento"]:
            score += w["Tipo"]
        if input_prob["Estación_Evento"] == case_prob["Estación_Evento"]:
            score += w["Estacion"]
        if input_prob["Grupo_Dietario"] == case_prob["Grupo_Dietario"]:
            score += w["Diet"]

        # Numerical similarity
        diff = abs(input_prob["Número_comensales"] - case_prob["Número_comensales"])
        pax_sim = max(0, 1 - diff / 500)
        score += pax_sim * w["Pax"]

        # Jaccard for prohibited ingredients
        s1 = set(input_prob["Ingredientes_prohibidos"])
        s2 = set(case_prob["Ingredientes_prohibidos"])
        union = len(s1 | s2)
        inter = len(s1 & s2)
        ing_sim = inter / union if union > 0 else 1
        score += ing_sim * w["Forbidden"]

        return score

    def retrieve(self, new_case):
        """Find the most similar case in the case base."""
        best_case = None
        best_score = -1

        print("\n[RETRIEVE] Computing similarities...")

        for case in self.case_base:
            score = self.similarity(new_case, case["problem"])
            print(f"   - Case {case['id']} → Score: {score:.4f}")

            if score > best_score:
                best_score = score
                best_case = case

        print(f"[RETRIEVE] Best Match: Case {best_case['id']} (score {best_score:.4f})")
        return best_case


# ============================================================
#                        2. REUSE
# ============================================================

class Reuser:
    def reuse(self, retrieved_case):
        """Select or adapt solution. (Here: simple reuse)"""
        print("[REUSE] Reusing solution from retrieved case.")
        return retrieved_case["solution"]


# ============================================================
#                        3. REVISE
# ============================================================

class Reviser:
    def revise(self, proposed_solution, new_case_problem):
        """
        Here you could adapt menus by removing forbidden ingredients, etc.
        For now, we return unchanged.
        """
        print("[REVISE] No revision rules applied. Returning proposed solution.")
        return proposed_solution


# ============================================================
#                        4. RETAIN
# ============================================================

class Retainer:
    def __init__(self, case_base):
        self.case_base = case_base

    def retain(self, problem, solution):
        """Stores new case in the knowledge base."""
        new_id = len(self.case_base) + 1
        new_case = {
            "id": new_id,
            "problem": problem,
            "solution": solution
        }
        self.case_base.append(new_case)

        print(f"[RETAIN] New case stored as ID {new_id}.")
        return new_case


# ============================================================
#                         MAIN CBR SYSTEM
# ============================================================

class MenuCBR:
    def __init__(self):
        self.case_base = []
        self._load_toy_data()

        # Instantiate 4R modules
        self.retriever = Retriever(self.case_base)
        self.reuser = Reuser()
        self.reviser = Reviser()
        self.retain_module = Retainer(self.case_base)

    # -------------------------------
    # Initial toy cases
    # -------------------------------
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

    # -------------------------------
    # Full 4R pipeline
    # -------------------------------
    def solve(self, query):
        print(f"\n======== NEW QUERY: {query['Tipo_de_Evento']} / {query['Grupo_Dietario']} ========")

        retrieved = self.retriever.retrieve(query)
        candidate = self.reuser.reuse(retrieved)
        revised = self.reviser.revise(candidate, query)
        retained = self.retain_module.retain(query, revised)

        return revised


# ============================================================
#                    EXECUTION EXAMPLE
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

print("\n--- RECOMMENDED MENU ---")
print(json.dumps(result, indent=2, ensure_ascii=False))

print(f"\n--- TOTAL CASES IN MEMORY: {len(cbr.case_base)} ---")
