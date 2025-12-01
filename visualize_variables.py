import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('recipes_extended.csv')

def classify_and_plot(df):
    var_types = {'numeric': [], 'categorical': [], 'boolean': []}
    
    for col in df.columns:
        # Check for Boolean (0/1 or True/False)
        if df[col].dropna().isin([0, 1]).all():
            var_types['boolean'].append(col)
        # Check for Categorical (String/Object OR Low Cardinality Numeric)
        elif df[col].dtype == 'object' or df[col].nunique() < 10:
            var_types['categorical'].append(col)
        # Default to Numeric (Continuous)
        elif np.issubdtype(df[col].dtype, np.number):
            var_types['numeric'].append(col)
            
    print(f"Detected Types: {var_types}")

    sns.set(style="whitegrid")

    # 2. Plotting Logic
    # A. Numeric: Histograms + Boxplots
    for col in var_types['numeric']:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        sns.histplot(df[col], kde=True, ax=axes[0], color='skyblue')
        axes[0].set_title(f'Distribution: {col}')
        sns.boxplot(x=df[col], ax=axes[1], color='lightgreen')
        axes[1].set_title(f'Boxplot: {col}')
        plt.tight_layout()
        plt.show()

    # B. Categorical: Bar Charts
    for col in var_types['categorical']:
        plt.figure(figsize=(10, 5))
        order = df[col].value_counts().index
        sns.countplot(y=df[col], order=order, palette='viridis')
        plt.title(f'Frequency: {col}')
        plt.show()

    # C. Boolean: Summary Bar Chart
    if var_types['boolean']:
        plt.figure(figsize=(10, 5))
        sums = df[var_types['boolean']].sum().sort_values(ascending=False)
        sns.barplot(x=sums.index, y=sums.values, palette='magma')
        plt.title('Count of "True" Flags (Boolean Variables)')
        plt.ylabel('Count')
        plt.show()

classify_and_plot(df)