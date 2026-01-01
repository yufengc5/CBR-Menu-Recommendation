'''
Script containing all main object classes

It contains INGREDIENT, DISH, MENU, QUERY, CASE and a TRIE implementation.
The TRIE implementation was meant for the frontend's word suggestion, but we
discarded it due to time constraints.
'''

from dataclasses import dataclass, replace, field
import math
from typing import List, Dict, Optional

# Transformer imports for LLM-based similarity
from sentence_transformers import SentenceTransformer
import torch
import torch.nn.functional as F

def jaccard(a, b):
        if not a and not b:
            return 1.0
        s1 = set([x.lower() for x in a])
        s2 = set([x.lower() for x in b])
        inter = len(s1 & s2)
        union = len(s1 | s2)
        return inter / union if union > 0 else 0.0

@dataclass
class Ingredient:
    name: str
    role: str = None  # e.g., "main", "secondary", "aroma", "fat"

    # Similarity placeholder, for now only name comparison
    def similarity(self, other : "Ingredient") -> float:
        if self.name.lower() == other.name.lower():
            return 1.0
        else:
            return 0.0

@dataclass
class Dish:
    name: str
    description: str
    ingredients: List[str]
    main_ingredient: str
    directions: List[str]
    techniques: List[str]
    cuisines: List[str]
    course_type: str
    tastes: List[str]
    primary_taste: str
    secondary_taste: str
    dietary_tags: List[str]
    prep_time: int
    cook_time: int
    cook_speed: str
    difficulty: str
    healthiness_score: int
    health_flags: list[str] = field(default_factory=list)
    health_level: str = "unknown"
    popularity: dict = field(default_factory=lambda: {"fast_hits": 0, "medium_hits": 0, "slow_hits": 0})
    justification: str = ""

    def similarity(self, other_dish):
        if not isinstance(other_dish, Dish):
            raise ValueError("Can only compare similarity with another Dish object, not with {}".format(type(other_dish)))

        raw_score = 0
        max_score = 0

        # Compare cuisines
        common_cuisines = jaccard(self.cuisines, other_dish.cuisines)
        raw_score += common_cuisines * 2
        max_score += 2

        # Compare tastes
        common_tastes = jaccard(self.tastes, other_dish.tastes)
        raw_score += common_tastes * 3
        max_score += 3

        # Compare ingredients
        common_ingredients = jaccard(self.ingredients, other_dish.ingredients)
        raw_score += common_ingredients * 4
        max_score += 4

        # Compare dietary tags
        common_dietary_tags = jaccard(self.dietary_tags, other_dish.dietary_tags)
        raw_score += common_dietary_tags * 2
        max_score += 2

        # Compare health flags
        common_health_flags = jaccard(self.health_flags, other_dish.health_flags)
        raw_score += common_health_flags * 2
        max_score += 2

        # Compare difficulty level (exact match)
        if self.difficulty == other_dish.difficulty:
            raw_score += 3
        max_score += 3

        # Compare healthiness score (normalized by distance between healthiness scores)
        health_score_diff = abs(self.healthiness_score - other_dish.healthiness_score)
        max_possible_health_score_diff = max(self.healthiness_score, other_dish.healthiness_score, 1)  # Avoid division by zero
        raw_score += 1 - health_score_diff / max_possible_health_score_diff
        max_score += 1

        # Compare primary tastes (exact match)
        if self.primary_taste == other_dish.primary_taste:
            raw_score += 5
        max_score += 5

        # Compare secondary tastes (exact match)
        if self.secondary_taste == other_dish.secondary_taste:
            raw_score += 3
        max_score += 3

        # Normalize the score: raw_score divided by max_score
        normalized_score = raw_score / max_score if max_score != 0 else 0.0
        
        return normalized_score
    
    def copy_with(self, **changes):
        return replace(self, **changes)
    
    def get_description(self) -> str:
        return str(self.description)

@dataclass
class Menu:
    first_course: Dish
    main_course: Dish
    dessert: Dish

    def similarity(self, other_menu: "Menu", i: int = 3) -> float:
        score = 0
        if (i == 0): return 1.0
        if (i > 0): score += self.first_course.similarity(other_menu.first_course)
        if (i > 1): score += self.main_course.similarity(other_menu.main_course)
        if (i > 2): score += self.dessert.similarity(other_menu.dessert)
        return score
    def __str__(self):
        return str([self.first_course.name, self.main_course.name, self.dessert.name])

class QueryComparatorLLM:
    '''
    LLM-based query comparison.
    By default uses sentence-transformers/all-MiniLM-L6-v2.
    '''
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def similarity(self, query1: "Query", query2: "Query") -> float:
        embeddings = self.model.encode([query1.description, query2.description], convert_to_tensor=True)
    
        similarity = F.cosine_similarity(
            embeddings[0].unsqueeze(0),
            embeddings[1].unsqueeze(0)
        )
    
        return similarity.item()

@dataclass
class Query:
    # Queries (what we will use to mass retrieve cases)
    event_type: str
    season: str
    number_of_guests: int
    techniques: List[str]
    presentation_style: str
    sensory_goals: List[str]

    # Refinement
    description: str  # Once we retrieve some cases, LLM similarity on description

    # Restrictions (constraints to adapt retrievals)
    culinary_traditions: List[str]
    dietary_group: List[str]
    forbidden_ingredients: List[str]
    prep_time: str
    healthiness_level: str

    def similarity(self, other_query: "Query") -> float:
        '''
        Only uses the fields that are marked as queries. The rest are for refinement or constraints.
        '''
        score = 0
        if self.event_type == other_query.event_type:
            score += 5
        
        if self.season == other_query.season:
            score += 5

        score -= math.log2(abs(self.number_of_guests - other_query.number_of_guests) + 1)
        
        score += jaccard(self.techniques, other_query.techniques) * 3
        
        if self.presentation_style == other_query.presentation_style:
            score += 4
        
        score += jaccard(self.sensory_goals, other_query.sensory_goals) * 2

        return score

@dataclass
class Case:
    id: int
    problem: Query
    solution: Menu
    rating: int = 5  # rating defaults to 5 for ground truth cases.

class CompressedTrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class CompressedTrie:
    def __init__(self):
        self.root = CompressedTrieNode()

    def insert(self, word):
        node = self.root
        while word:
            # Find if any child edge matches a prefix of the word
            for edge in node.children:
                common_prefix_len = self._common_prefix_length(edge, word)
                if common_prefix_len > 0:
                    # Split edge if needed
                    if common_prefix_len < len(edge):
                        # Split the edge
                        existing_child = node.children.pop(edge)
                        new_child = CompressedTrieNode()
                        new_child.children[edge[common_prefix_len:]] = existing_child
                        new_child.is_end = existing_child.is_end if common_prefix_len == len(word) else False
                        node.children[edge[:common_prefix_len]] = new_child
                        node = new_child
                    else:
                        node = node.children[edge]
                    word = word[common_prefix_len:]
                    break
            else:
                # No matching edge, add a new child
                node.children[word] = CompressedTrieNode()
                node.children[word].is_end = True
                return
        node.is_end = True

    def _common_prefix_length(self, s1, s2):
        """Return the length of the common prefix of s1 and s2"""
        i = 0
        while i < min(len(s1), len(s2)) and s1[i] == s2[i]:
            i += 1
        return i

    def autocomplete(self, prefix):
        node = self.root
        path = prefix

        while prefix:
            for edge, child in node.children.items():
                if edge.startswith(prefix):
                    # The edge fully matches the prefix, return all words from here
                    return self._dfs(child, path[:-len(prefix)] + edge)
                elif prefix.startswith(edge):
                    # The edge is a prefix of the remaining prefix, go deeper
                    node = child
                    prefix = prefix[len(edge):]
                    break
            else:
                # No matching edges
                return []
        
        # If prefix is exhausted
        return self._dfs(node, path)

    def _dfs(self, node, prefix):
        """Depth-first search to collect all words under this node"""
        results = []
        if node.is_end:
            results.append(prefix)
        for edge, child in node.children.items():
            results.extend(self._dfs(child, prefix + edge))
        return results
