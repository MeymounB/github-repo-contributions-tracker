import os
from dotenv import load_dotenv
import pandas as pd
from github_api.rest import fetch_user_repos
from github_api.graphql import fetch_contributed_repos_graphql
from utils.display import add_blank_rows, generate_table

# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

# Lire les variables d'environnement
TOKEN = os.getenv("GITHUB_TOKEN")
SORT_BY = os.getenv("SORT_BY", "Owner")
BETTER_READABILITY = os.getenv("BETTER_READABILITY", "true").lower() == "true"
CONTRIBUTION_TYPES = os.getenv("CONTRIBUTION_TYPES", "all").replace(" ", "").lower().split(",")
HAS_ACCESS_ONLY = os.getenv("HAS_ACCESS_ONLY", "false").lower() == "true"
VISIBILITY = os.getenv("VISIBILITY", "both").lower()

if not TOKEN:
    raise ValueError("GitHub token not found. Please set GITHUB_TOKEN in your .env file.")

# Sortie de débogage
print(f"Using GitHub token: {TOKEN[:4]}... (hidden for security)")
print(f"Sorting by: {SORT_BY}")
print(f"Better readability: {BETTER_READABILITY}")
print(f"Contribution types: {CONTRIBUTION_TYPES}")
print(f"Has access only: {HAS_ACCESS_ONLY}")
print(f"Visibility: {VISIBILITY}")

def display_repos(sorted_by, better_readability):
    """Récupérer et afficher les dépôts dans un format trié et lisible."""
    repos = fetch_user_repos(TOKEN, VISIBILITY) if HAS_ACCESS_ONLY else []
    if not HAS_ACCESS_ONLY:
        contributed_repos = fetch_contributed_repos_graphql(TOKEN, VISIBILITY)
        repos.extend(contributed_repos)

    # Filtrer les doublons
    df = pd.DataFrame(repos).drop_duplicates(subset='Name')

    if df.empty:
        print("No repositories found.")
        return

    # Vérifier que la colonne de tri existe dans le DataFrame
    if sorted_by in df.columns:
        # Trier le DataFrame
        df = df.sort_values(by=sorted_by)

    # Ajouter des lignes vides entre les différents préfixes de nom
    df = add_blank_rows(df, sorted_by, better_readability)

    print(df.to_string(index=False))

    # Générer une représentation graphique du tableau
    generate_table(df)

# Définir les critères de tri ici: "Name", "Visibility", "Owner", "Is Fork", ou "Original Owner"
display_repos(SORT_BY, BETTER_READABILITY)
