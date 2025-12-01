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
        """Computes a weighted similarity score between 0 and 1."""
        score = 0.0
        
        w = self.weights

        # Title, Season, Diet: exact match
        if case1["Tipo_de_Evento"] == case2["Tipo_de_Evento"]:
            score += w["Tipo"]
        if case1["Estación_Evento"] == case2["Estación_Evento"]:
            score += w["Estacion"]
        if case1["Grupo_Dietario"] == case2["Grupo_Dietario"]:
            score += w["Diet"]

        # Numerical similarity
        diff = abs(case1["Número_comensales"] - case2["Número_comensales"])
        pax_sim = max(0, 1 - diff / 500)
        score += pax_sim * w["Pax"]

        # Jaccard for prohibited ingredients
        s1 = set(case1["Ingredientes_prohibidos"])
        s2 = set(case2["Ingredientes_prohibidos"])
        union = len(s1 | s2)
        inter = len(s1 & s2)
        ing_sim = inter / union if union > 0 else 1
        score += ing_sim * w["Forbidden"]

        return score

    def retrieve_one(self, new_case):
        """Find the most similar case in the case base."""
        best_case = None
        best_score = -1

        print("\n[RETRIEVE] Computing similarities...")

        for case in self.case_base:
            score = self.similarity(new_case, case["problem"])
            print(f"   - Case {case['id']} -> Score: {score:.4f}")

            if score > best_score:
                best_score = score
                best_case = case

        print(f"[RETRIEVE] Best Match: Case {best_case['id']} (score {best_score:.4f})")
        return best_case
    
    def retrieve_top(self, new_case, top_n=4):
        """Find the top n cases to the base case."""
        best_cases = [(None, -1)] * top_n

        print("\n[RETRIEVE] Computing similarities...")

        for case in self.case_base:
            score = self.similarity(new_case, case["problem"])
            print(f"   - Case {case['id']} -> Score: {score:.4f}")

            if score > best_cases[-1][1]:
                best_cases[-1] = (case, score)
                best_cases.sort(key=lambda x: x[1], reverse=True)

        print(f"[RETRIEVE] Retrieved top {top_n} cases.")
        total_weight = sum(score for case, score in best_cases if case is not None)
        return [(case, score / total_weight) for case, score in best_cases]


# ============================================================
#                        2. REUSE
# ============================================================

class Reuser:
    def simple_reuse(self, retrieved_cases, query):
        """Select or adapt solution. (Here: simple reuse)"""
        print("[REUSE] Reusing solution from retrieved case.")
        return retrieved_cases[0][0]["solution"]
    
    def weighted_reuse(self, retrieved_cases, rejects=None):
        """Returns a new possible solution based on past cases, merged and sampled according to their similarity weights.
        
        ### PARAMETERS:
        - retrieved_cases: List of tuples (case, weight) retrieved from the case base.
        - rejects: Tuple of previously rejected solutions and their issue (case, problem),
          where problem describes why it was rejected (Primero, Segundo, Postre, Otro).
        """
        print("[REUSE] Creating possible solution.")
        
        new_case ={ "Platos": {
                        "Primero": {"Nombre": ""},
                        "Segundo": {"Nombre": ""},
                        "Postre": {"Nombre": ""}}
                  }

        for course in new_case["Platos"].keys():
            # Impose restrictions based on query
            
            # For now, we skip this step and directly sample from retrieved cases
            # We would need dish information to filter based on ingredients, diet, etc.

            # Select dish from retrieved cases based on weights and try to avoid similarity with rejects
            if rejects:
                filtered_cases = []
                # Filter out cases that were rejected for this course or others
                for case in retrieved_cases:
                    is_rejected = False
                    for rej_case, rej_problem in rejects:
                        if rej_problem == course:
                            if case[0]["solution"]["Platos"][course]["Nombre"] == rej_case["Platos"][course]["Nombre"]:
                                is_rejected = True
                                break
                        elif rej_problem == "Otro":  # Consider with lower weight
                            if case[0]["solution"]["Platos"][course]["Nombre"] == rej_case["Platos"][course]["Nombre"]:
                                weights_index = retrieved_cases.index(case)
                                reduced_weight = retrieved_cases[weights_index][1] * 0.5
                                retrieved_cases[weights_index] = (case[0], reduced_weight)
                        else:
                            continue
                                
                    if not is_rejected:
                        filtered_cases.append(case)
            else:
                filtered_cases = retrieved_cases
            
            if not filtered_cases:
                print("[REUSE] No valid cases available after filtering rejects.")
                return None  # No valid cases to choose from
            
            print("RETRIEVE", retrieved_cases)
            print("Filtered_cases", filtered_cases)

            dishes = [case[0][0]["solution"]["Platos"][course]["Nombre"] for case in filtered_cases]
            weights = [case[1] for case in filtered_cases]
            total = sum(weights)
            weights = [w / total for w in weights]  # Normalize
            selected_dish = random.choices(dishes, weights=weights, k=1)[0]
            new_case["Platos"][course]["Nombre"] = selected_dish

        return new_case


# ============================================================
#                        3. REVISE
# ============================================================

class Reviser:
    def revise(self, proposed_solution, query, alternatives, rejects=None):
        """
        Here we apply feedback to the proposed solution.

        ### PARAMETERS:
        - proposed_solution: The menu proposed by the Reuser.
        - query: The original problem description.
        - alternatives: List of alternative solutions proposed (case, weight).
        - rejects: List of previously rejected solutions.
        """

        # Ask user for feedback
        print("[REVISE] Presenting proposed solution for review.")
        print(json.dumps(proposed_solution, indent=2, ensure_ascii=False))
        feedback = input("Do you accept this menu? ([Y]/n): ").strip().lower()
        if feedback == 'n':
            print("[REVISE] User rejected the proposed solution. (Proposing new solution.)")
            rejects = rejects + [proposed_solution] if rejects else [proposed_solution]
            new_solution = self.reuser.weighted_reuse(alternatives, rejects)
            return self.revise(new_solution, query, alternatives, rejects)

        print("[REVISE] Returning revised solution.")
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

        retrieved = self.retriever.retrieve_one(query)
        candidate = self.reuser.weighted_reuse(retrieved, rejects=None)
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
