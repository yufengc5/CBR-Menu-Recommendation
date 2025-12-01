import pandas as pd
import numpy as np
import ast 

# 1. Load the Dataset
file_path = 'recipes_extended.csv' 
df = pd.read_csv(file_path)

print(f"Original shape: {df.shape}")

# 2. Parse List Columns
list_cols = ['ingredients', 'cuisine_list', 'course_list', 'tastes', 'dietary_profile']

def safe_parse(val):
    try:
        if isinstance(val, list):
            return val
        if isinstance(val, str) and val.startswith('[') and val.endswith(']'):
            return ast.literal_eval(val)
        return []
    except (ValueError, SyntaxError):
        return []

for col in list_cols:
    if col in df.columns:
        df[col] = df[col].apply(safe_parse)

# 3. Handling Missing or Noisy Data
if 'num_ingredients' in df.columns and 'num_steps' in df.columns:
    df = df[(df['num_ingredients'] > 0) & (df['num_steps'] > 0)]

# Impute missing numeric values (Time) with the median
time_cols = ['est_prep_time_min', 'est_cook_time_min']
for col in time_cols:
    if col in df.columns:
        df[col] = df[col].fillna(df[col].median())

# Create a 'total_time' feature (useful for "quick meal" preferences)
df['total_time_min'] = df['est_prep_time_min'] + df['est_cook_time_min']

# 4. Encoding Ordinal Features (Difficulty)
difficulty_map = {'easy': 1, 'medium': 2, 'hard': 3}

# Normalize text first (lowercase)
df['difficulty'] = df['difficulty'].str.lower().str.strip()
df['difficulty_score'] = df['difficulty'].map(difficulty_map)

# Fill missing difficulty with 'medium' (2)
df['difficulty_score'] = df['difficulty_score'].fillna(2).astype(int)

# 5. Clean Course / Category for Menu Planning
# We need to know if a dish is a "Main", "Dessert", or "Starter".
# 'course_list' might contain multiple tags. We can extract a primary course or create flags.
target_courses = ['main dish', 'dessert', 'appetizer', 'soup', 'salad', 'side dish']

def extract_primary_course(courses):
    # Normalize list
    courses_lower = [c.lower() for c in courses]
    for target in target_courses:
        # Simple heuristic: return the first matching target course found
        for c in courses_lower:
            if target in c:
                return target
    return 'other'

df['primary_course'] = df['course_list'].apply(extract_primary_course)

# 6. Boolean Flags for Constraints
bool_cols = ['is_vegan', 'is_vegetarian', 'is_halal', 'is_kosher', 'is_gluten_free', 'is_dairy_free', 'is_nut_free']
for col in bool_cols:
    if col in df.columns:
        df[col] = df[col].astype(int)

# 7. Feature Selection for Case Base
# Select only columns useful for the Recommender (Retrieval & Similarity)
selected_columns = [
    'recipe_title', 
    'description',
    'ingredients',          # For content-based similarity
    'primary_course',       # For menu structure (Main vs Dessert)
    'cuisine_list',         # For user preferences
    'difficulty_score',     # For restriction (Expertise level)
    'total_time_min',       # For restriction (Time available)
    'healthiness_score',    # For preference
    'primary_taste',        # For preference (sweet, spicy)
] + bool_cols               # For hard constraints

# Filter dataset to selected columns (keep original ID or index)
case_base = df[selected_columns].copy()

# Remove duplicates if any
case_base = case_base.drop_duplicates(subset=['recipe_title'])

print(f"Final Case Base shape: {case_base.shape}")
print(case_base.head())

# Save preprocessed data
case_base.to_csv('preprocessed_recipes_cbr.csv', index=False)