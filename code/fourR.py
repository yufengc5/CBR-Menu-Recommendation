import math
from objectclasses import Case, Query, Dish, Menu, jaccard
import heapq
import random
#from transformers import DistilBertTokenizer, DistilBertModel
#import torch
from sklearn.metrics.pairwise import cosine_similarity

class Retriever:
    def __init__(self, case_base):
        self.case_base = case_base

    def retrieve_top(self, new_case: Query, top_n=4):
        """Retrieve the top-N most similar cases"""
        
        print("\n[RETRIEVE] Computing similarities...")

        heap = []  # min-heap storing (score, case)

        for i, case in self.case_base.items():
            score = new_case.similarity(case.problem)

            if len(heap) < top_n + 1:
                heapq.heappush(heap, (score, i))
            else:
                # Only push if this score is better than the smallest score in heap
                if score > heap[0][0]:
                    heapq.heapreplace(heap, (score, i))
        print(f"[RETRIEVE] Retrieved top {top_n} cases.")

        offset = offset = -heap[0][0] if heap else 0
        # Normalize in one pass
        total_weight = sum(score + offset for score, _ in heap)
        inv_total = 1.0 / total_weight

        # Convert to (case, normalized_score)
        results = [(case, (score + offset) * inv_total) for score, case in heap]
        # Return sorted highest -> lowest (optional but nice)
        return sorted(results, key=lambda x: x[1], reverse=True)[:top_n]


class Reuser:
    def __init__(self, query, dishlist):
        self.query = query
        self.dishlist = dishlist

    def _apply_constraints(self, dishlist: list[Dish]) -> list[Dish]:
        culinary_traiditions = self.query.culinary_tradition
        dietary_group = self.query.dietary_group
        forbidden_ingredients = self.query.forbidden_ingredients
        prep_time = self.query.prep_time

        return dishlist
    
    def _mutate(self, dish : Dish):
        dishes, weights = self._get_weighted_knn()
        return random.choice(dishes, weights=weights)
    
    def _get_weighted_knn(self, dish: Dish, n: int) -> tuple[list[str], list[float]]:
        heap = []
        total_similarity = 0
        
        # Calculate similarities and push them into the heap
        for d in self.dishlist.values():
            if d == dish:
                continue
            sim = dish.similarity(d)
            heapq.heappush(heap, (-sim, d.name))
            total_similarity += sim
        
        closest_dish_names = []
        normalized_similarities = []
        for _ in range(n):
            sim, d = heapq.heappop(heap)
            normalized_sim = -sim / total_similarity  # Normalize similarity
            closest_dish_names.append(d)
            normalized_similarities.append(normalized_sim)
        
        return closest_dish_names, normalized_similarities
        
    
    def reuse(self, retrieved_cases : list[tuple[Case, float]], rejects=None) -> Menu:
        '''
        Takes in a list of retrieved cases and their weights, as well as previously rejected cases and the reason why,
        and outputs a menu proposal. It does this by referencing from past experiences as well as experimenting with new dishes.
        '''
        print("[REUSE] Creating possible solution.")

        new_case = Menu(first_course=None, main_course=None, dessert=None)

        for index, course in enumerate(["first_course", "main_course", "dessert"]):
            adjusted_cases = []

            for case, weight in retrieved_cases:
                dish_name = getattr(case.solution, course).name
                penalty = 1.0

                if self.query.healthiness_level == "healthy":  # penalize unhealthy dishes
                    penalty *= (self.dishlist[dish_name].healthiness_score / 100)
                elif self.query.healthiness_level == "moderate":  # penalize sqrt of unhealthy dishes
                    penalty *= math.sqrt(self.dishlist[dish_name].healthiness_score / 100)

                if rejects:
                    for rejected_solution, reason in rejects:
                        reason = reason.lower()

                        if reason == course.lower():
                            bad_dish = getattr(rejected_solution, course).name
                            if dish_name == bad_dish:
                                penalty = 0
                            else:
                                penalty = 1 - self.dishlist[dish_name].similarity(self.dishlist[bad_dish])**2

                        elif reason in ("first_course", "main_course", "dessert"):
                            continue

                        elif reason == "others":
                            penalty *= 0.5

                menu_similarity = case.solution.similarity(new_case, i=index)
                penalty *= menu_similarity*2

                if penalty > 0 and dish_name:
                    adjusted_cases.append((case, weight * penalty))

            if not adjusted_cases:
                print(f"[REUSE] No valid cases for course '{course}' after rejection filtering.")
                return None

            dishes = [getattr(c.solution, course) for c, _ in adjusted_cases]
            weights = [w for _, w in adjusted_cases]

            total = sum(weights)
            if total <= 0:
                weights = [1/len(weights)] * len(weights)
            else:
                weights = [w / total for w in weights]

            selected = random.choices(dishes, weights=weights, k=1)[0]
            setattr(new_case, course, selected)

        return new_case


class Reviser:
    def __init__(self, reuser):
        self.reuser = reuser

    def revise(self, proposed_solution : Menu, query : Query, alternatives : tuple[Menu, float], rejects=None) -> Menu:

        if proposed_solution is None:
            print("[REVISE] No further solutions possible.")
            return None

        print("\n[REVISE] Proposed Menu:")
        print(proposed_solution)

        try:
            feedback = input("Do you accept this menu? ([Y]/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            feedback = 'y'

        if feedback == 'n':
            print("[REVISE] Solution rejected.")
            try:
                feedback_reason = input("What was wrong with the menu? (first_course, main_course, dessert, others): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                feedback_reason = "others"
            rejects = rejects + [(proposed_solution, feedback_reason)] if rejects else [(proposed_solution, feedback_reason)]
            new_solution = self.reuser.reuse(alternatives, rejects)
            return self.revise(new_solution, query, alternatives, rejects)

        print("[REVISE] Accepted final solution.")
        return proposed_solution


class Retainer:
    def __init__(self, case_base):
        self.case_base = case_base

    def retain(self, problem, solution):
        new_id = len(self.case_base) + 1
        new_case = Case(id=new_id, problem=problem, solution=solution)
        self.case_base.append(new_case)
        print(f"[RETAIN] Stored new case ID {new_id}.")
        return new_case
