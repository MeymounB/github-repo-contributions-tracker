import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GitHub GraphQL endpoint
URL = "https://api.github.com/graphql"

# Read the GitHub personal access token and sorting criteria from .env
TOKEN = os.getenv("GITHUB_TOKEN")
SORT_BY = os.getenv("SORT_BY", "Owner")
BETTER_READABILITY = os.getenv("BETTER_READABILITY", "true").lower() == "true"

if not TOKEN:
    raise ValueError("GitHub token not found. Please set GITHUB_TOKEN in your .env file.")

# Debugging output
print(f"Using GitHub token: {TOKEN[:4]}... (hidden for security)")
print(f"Sorting by: {SORT_BY}")
print(f"Better readability: {BETTER_READABILITY}")

# GraphQL query template
QUERY = """
query ($cursor: String) {
  viewer {
    repositoriesContributedTo(first: 100, contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY], includeUserRepositories: true, after: $cursor) {
      totalCount
      nodes {
        nameWithOwner
        isPrivate
        isFork
        parent {
          nameWithOwner
          owner {
            login
          }
        }
        owner {
          login
        }
      }
      pageInfo {
        endCursor
        hasNextPage
      }
    }
  }
}
"""

HEADERS = {
    "Authorization": f"Bearer {TOKEN}"
}

def run_query(query, variables):
    """Run a GraphQL query with the given variables."""
    response = requests.post(URL, json={'query': query, 'variables': variables}, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

def fetch_repos():
    """Fetch all repositories the user has contributed to."""
    all_repos = []
    cursor = None
    has_next_page = True

    while has_next_page:
        variables = {"cursor": cursor}
        result = run_query(QUERY, variables)
        
        if 'errors' in result:
            for error in result['errors']:
                if error['type'] == 'FORBIDDEN' and 'saml_failure' in error['extensions']:
                    print(f"Skipping repository due to SAML enforcement: {error['message']}")
                else:
                    raise Exception(f"GraphQL query error: {error}")
        
        repos = result['data']['viewer']['repositoriesContributedTo']['nodes']
        
        if repos is None:
            raise Exception("Failed to fetch repositories. The 'nodes' field is None.")
        
        all_repos.extend(repos)
        page_info = result['data']['viewer']['repositoriesContributedTo']['pageInfo']
        cursor = page_info['endCursor']
        has_next_page = page_info['hasNextPage']

    return all_repos

def add_blank_rows(df, sorted_by, better_readability):
    """Add blank rows for better readability."""
    blank_row = pd.DataFrame([["_", "_", "_", "_", "_"]], columns=df.columns)
    new_df = pd.DataFrame(columns=df.columns)
    current_prefix = None
    for _, row in df.iterrows():
        name_prefix = row[sorted_by]
        if name_prefix != current_prefix:
            if current_prefix is not None:
                new_df = pd.concat([new_df, blank_row], ignore_index=True)
                if better_readability:
                    new_df = pd.concat([new_df, blank_row], ignore_index=True)
            current_prefix = name_prefix
        new_df = pd.concat([new_df, pd.DataFrame([row], columns=df.columns)], ignore_index=True)
    return new_df

def display_repos(sorted_by, better_readability):
    """Fetch and display repositories in a sorted and readable format."""
    repos = fetch_repos()

    data = []
    for repo in repos:
        if repo is not None:
            data.append({
                "Name": repo['nameWithOwner'],
                "Visibility": "Private" if repo['isPrivate'] else "Public",
                "Owner": repo['owner']['login'],
                "Is Fork": "Yes" if repo['isFork'] else "No",
                "Original Owner": repo['parent']['owner']['login'] if repo['isFork'] and repo['parent'] else "_"
            })

    df = pd.DataFrame(data)

    # Sorting the DataFrame
    if sorted_by in ["Name", "Visibility", "Owner", "Is Fork", "Original Owner"]:
        df = df.sort_values(by=sorted_by)

    # Adding blank rows between different name prefixes
    df = add_blank_rows(df, sorted_by, better_readability)

    print(df.to_string(index=False))
    
    # Generate a graphical representation of the table
    num_rows, num_cols = df.shape
    fig, ax = plt.subplots(figsize=(num_cols * 3, num_rows * 0.5))  # Adjust the figure size as needed
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)  # Set font size

    # Adjust column widths and text alignment
    for key, cell in table.get_celld().items():
        cell.set_text_props(fontsize=10)
        cell.set_height(0.04)
        cell.set_width(0.3 if key[1] == 0 else 0.15)
        if key[1] == 0:  # Left-align the 'Name' column
            cell.set_text_props(ha='left')
        if key[0] > 0 and key[1] == 3 and cell.get_text().get_text() == "Yes":  # Highlight 'Yes' in 'Is Fork'
            cell.set_text_props(fontweight='bold', color='red')

    # Save the figure
    plt.savefig("repos_table.png", bbox_inches='tight')
    plt.show()

# Set the sorting criteria here: "Name", "Visibility", "Owner", "Is Fork", or "Original Owner"
display_repos(SORT_BY, BETTER_READABILITY)
