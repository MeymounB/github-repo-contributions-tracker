import requests
import time

HEADERS = {
    "Accept": "application/vnd.github.v3+json"
}

def run_request(url, token, params=None):
    """Exécuter une requête API GitHub."""
    headers = {"Authorization": f"Bearer {token}", **HEADERS}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 422:
        print(f"Reached pagination limit: {response.text}")
        return None
    elif response.status_code == 403 and response.headers.get('X-RateLimit-Remaining') == '0':
        reset_time = int(response.headers.get('X-RateLimit-Reset'))
        sleep_time = reset_time - time.time()
        print(f"Rate limit exceeded, sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
        return run_request(url, token, params)
    else:
        raise ValueError(f"Request failed with status code {response.status_code}: {response.text}")

def fetch_user_repos(token, visibility):
    """Récupérer tous les dépôts auxquels l'utilisateur a accès."""
    repos = []
    page = 1
    while True:
        url = "https://api.github.com/user/repos"
        params = {"page": page, "per_page": 100}
        result = run_request(url, token, params)
        if not result:
            break
        for repo in result:
            if (visibility == "both" or 
               (visibility == "public" and not repo["private"]) or 
               (visibility == "private" and repo["private"])):
                repos.append({
                    "Name": repo["full_name"],
                    "Visibility": "Private" if repo["private"] else "Public",
                    "Owner": repo["owner"]["login"],
                    "Is Fork": "Yes" if repo["fork"] else "No",
                    "Original Owner": repo["parent"]["owner"]["login"] if repo["fork"] and "parent" in repo else "_",
                    "Contribution Type": "access"
                })
        if len(result) < 100:
            break
        page += 1
    return repos
