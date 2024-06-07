import pandas as pd
import matplotlib.pyplot as plt

def add_blank_rows(df, sorted_by, better_readability):
    """Ajouter des lignes vides pour une meilleure lisibilité."""
    blank_row = pd.DataFrame([["_", "_", "_", "_", "_", "_"]], columns=df.columns)
    new_df = pd.DataFrame(columns=df.columns)
    current_prefix = None
    for _, row in df.iterrows():
        name_prefix = row[sorted_by]
        if name_prefix != current_prefix:
            if current_prefix is not None:
                new_df = pd.concat([new_df, blank_row], ignore_index=True)
                if better_readability and sorted_by in ["Visibility", "Is Fork", "Original Owner"]:
                    new_df = pd.concat([new_df, blank_row], ignore_index=True)
            current_prefix = name_prefix
        new_df = pd.concat([new_df, pd.DataFrame([row], columns=df.columns)], ignore_index=True)
    return new_df

def generate_table(df):
    """Générer une représentation graphique du tableau."""
    num_rows, num_cols = df.shape
    _, ax = plt.subplots(figsize=(num_cols * 3, num_rows * 0.5))  # Ajuster la taille de la figure si nécessaire
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center', colLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)  # Définir la taille de la police

    # Ajuster la largeur des colonnes et l'alignement du texte
    for key, cell in table.get_celld().items():
        cell.set_text_props(fontsize=10)
        cell.set_height(0.04)
        cell.set_width(0.3 if key[1] == 0 else 0.15)
        if key[1] == 0:  # Aligner à gauche la colonne 'Name'
            cell.set_text_props(ha='left')
        if key[0] > 0 and key[1] == 3 and cell.get_text().get_text() == "Yes":  # Mettre en évidence 'Yes' dans 'Is Fork'
            cell.set_text_props(fontweight='bold', color='red')

    # Enregistrer la figure
    plt.savefig("repos_table.png", bbox_inches='tight')
    plt.show()
