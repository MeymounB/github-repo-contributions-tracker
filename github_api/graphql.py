import requests

HEADERS = {
    "Accept": "application/vnd.github.v3+json"
}

def run_graphql_query(query, token, variables=None):
    """Exécuter une requête GraphQL."""
    headers = {"Authorization": f"Bearer {token}", **HEADERS}
    response = requests.post("https://api.github.com/graphql", json={'query': query, 'variables': variables}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError(f"Query failed with status code {response.status_code}: {response.text}")

def fetch_contributed_repos_graphql(token, visibility):
    """Récupérer tous les dépôts auxquels l'utilisateur a contribué via l'API GraphQL."""
    query = """
    {
      viewer {
        contributionsCollection {
          commitContributionsByRepository {
            repository {
              nameWithOwner
              isPrivate
              isFork
              owner {
                login
              }
              parent {
                owner {
                  login
                }
              }
            }
          }
          pullRequestContributionsByRepository {
            repository {
              nameWithOwner
              isPrivate
              isFork
              owner {
                login
              }
              parent {
                owner {
                  login
                }
              }
            }
          }
          issueContributionsByRepository {
            repository {
              nameWithOwner
              isPrivate
              isFork
              owner {
                login
              }
              parent {
                owner {
                  login
                }
              }
            }
          }
          repositoryContributions(first: 100) {
            nodes {
              repository {
                nameWithOwner
                isPrivate
                isFork
                owner {
                  login
                }
                parent {
                  owner {
                    login
                  }
                }
              }
            }
          }
          pullRequestReviewContributions(first: 100) {
            nodes {
              repository {
                nameWithOwner
                isPrivate
                isFork
                owner {
                  login
                }
                parent {
                  owner {
                    login
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    result = run_graphql_query(query, token)
    if 'data' not in result or 'viewer' not in result['data']:
        print("Error: Unexpected response structure.")
        print(result)
        return []

    repos = {}
    contribution_map = {
        "commitContributionsByRepository": "commit",
        "pullRequestContributionsByRepository": "pr",
        "issueContributionsByRepository": "issue",
        "repositoryContributions": "repo",
        "pullRequestReviewContributions": "review"
    }

    for contribution_type, type_acronym in contribution_map.items():
        contributions = result["data"]["viewer"]["contributionsCollection"].get(contribution_type, [])
        nodes = contributions if isinstance(contributions, list) else contributions.get("nodes", [])
        for node in nodes:
            repo = node["repository"]
            if (visibility == "both" or 
               (visibility == "public" and not repo["isPrivate"]) or 
               (visibility == "private" and repo["isPrivate"])):
                repo_name = repo["nameWithOwner"]
                if repo_name not in repos:
                    repos[repo_name] = {
                        "Name": repo_name,
                        "Visibility": "Private" if repo["isPrivate"] else "Public",
                        "Owner": repo["owner"]["login"],
                        "Is Fork": "Yes" if repo["isFork"] else "No",
                        "Original Owner": repo["parent"]["owner"]["login"] if repo["isFork"] and repo.get("parent") else "_",
                        "Contribution Type": set()
                    }
                repos[repo_name]["Contribution Type"].add(type_acronym)

    # Convertir les types de contributions en chaîne de caractères
    for repo in repos.values():
        repo["Contribution Type"] = ", ".join(sorted(repo["Contribution Type"]))

    return list(repos.values())
