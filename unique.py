#!/usr/bin/env python3
import pandas as pd
import ast

# ---------------------------------------------------------
# Helper: safely parse list-like strings
# ---------------------------------------------------------
def parse_list(value):
    if isinstance(value, list):
        return value
    if pd.isna(value):
        return []
    try:
        return ast.literal_eval(value)
    except:
        return []


# ---------------------------------------------------------
# Main script
# ---------------------------------------------------------

def main():
    print("\n=== Unique Value Extractor ===\n")

    csv_path = input("CSV filename (e.g., recipes.csv): ").strip()
    if csv_path == "":
        print("❌ No file provided.")
        return

    print("\n📥 Loading CSV…")
    df = pd.read_csv(csv_path)
    print(f"➡️ Loaded {len(df)} rows, {len(df.columns)} columns.\n")

    print("\n🔍 Extracting unique values per variable:\n")

    for col in df.columns:
        print("\n-----------------------------------------------------")
        print(f"📌 COLUMN: {col}")
        print("-----------------------------------------------------")

        sample_value = df[col].iloc[0]

        # ---------- Case 1: column contains list-like strings ----------
        if isinstance(sample_value, str) and sample_value.startswith("[") and sample_value.endswith("]"):
            unique_items = set()

            for v in df[col]:
                items = parse_list(v)
                for it in items:
                    unique_items.add(str(it).strip())

            print(f"Unique items ({len(unique_items)}):")
            for u in sorted(unique_items):
                print("  -", u)

        # ---------- Case 2: normal scalar column ----------
        else:
            uniques = df[col].dropna().unique()
            print(f"Unique values ({len(uniques)}):")
            for u in uniques:
                print("  -", u)

    print("\n🎉 DONE — all unique values printed.\n")


if __name__ == "__main__":
    main()
