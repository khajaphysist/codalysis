import os
import git
import urllib.parse
from typing import List, Optional
from repository import Repository
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import requests
from pick import pick

class RepoManager:
    """
    Manages cloning and updating git repositories.
    """
    def __init__(self, data_dir: str = "./data", repository_urls: List[str] = [], group_url: str = None):
        """
        Initializes the RepoManager and syncs the provided repositories.

        Args:
            data_dir (str): The base directory for cloning repositories.
            repository_urls (List[str]): A list of git repository URLs to sync.
        """
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.metadata_file = os.path.join(self.data_dir, "repos_metadata.json")
        self.repos: List[Repository] = self._load_metadata()

        group_urls = []
        if group_url:
            group_urls = fetch_repos_under_group(group_url)
            if group_urls:
                group_urls = filter_repos_according_to_user(group_urls)


        # Combine URLs from metadata and provided URLs, removing duplicates
        all_urls = list(set([repo.url for repo in self.repos] + repository_urls + group_urls))

        if all_urls:
            self.sync_repositories(all_urls)


    def _load_metadata(self) -> List[Repository]:
        """
        Loads repository metadata from the JSON file.

        Returns:
            List[Repository]: A list of Repository dataclass objects.
        """
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "r") as f:
                    metadata = json.load(f)
                    return [Repository(**repo_data) for repo_data in metadata]
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error loading repository metadata from {self.metadata_file}: {e}")
                return []
        return []


    def _clone_or_pull_repository(self, url: str) -> Optional[Repository]:
        """
        Clones a single repository or pulls updates if it already exists.

        Args:
            url (str): The URL of the repository.

        Returns:
            Optional[Repository]: A Repository dataclass object if successful, None otherwise.
        """
        parsed_url = urllib.parse.urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            print(f"Skipping invalid repository URL: {url}")
            return None

        group_name = path_parts[-2]
        repo_name = path_parts[-1].replace('.git', '')
        repo_path = os.path.join(self.data_dir, group_name, repo_name)

        if os.path.exists(repo_path):
            print(f"Repository already exists: {group_name}/{repo_name}. Performing git pull...")
            try:
                repo = git.Repo(repo_path)
                origin = repo.remotes.origin
                origin.pull()
                print(f"Successfully pulled latest changes for {group_name}/{repo_name}")
                return Repository(url=url, group_name=group_name, repo_name=repo_name, repo_path=repo_path)
            except Exception as e:
                print(f"Error pulling changes for {group_name}/{repo_name}: {e}")
                return None
        else:
            print(f"Cloning {group_name}/{repo_name} from {url}...")
            try:
                git.Repo.clone_from(url, repo_path)
                print(f"Successfully cloned {group_name}/{repo_name}")
                return Repository(url=url, group_name=group_name, repo_name=repo_name, repo_path=repo_path)
            except Exception as e:
                print(f"Error cloning {group_name}/{repo_name}: {e}")
                return None

    def sync_repositories(self, repository_urls: List[str], max_workers: int = 5) -> List[Repository]:
        """
        Clones a list of git repositories into the ./data directory concurrently.
        If a repository already exists, it performs a git pull to update it.

        Args:
            repository_urls (List[str]): A list of git repository URLs.
            max_workers (int): The maximum number of threads to use for cloning.

        Returns:
            List[Repository]: A list of Repository dataclass objects for the cloned repositories.
        """
        synced_repos: List[Repository] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self._clone_or_pull_repository, url): url for url in repository_urls}
            for future in as_completed(future_to_url):
                repo = future.result()
                if repo:
                    synced_repos.append(repo)

        # Update the internal list of repositories
        synced_urls = {repo.url for repo in synced_repos}
        existing_repos = [repo for repo in self.repos if repo.url not in synced_urls]
        self.repos = existing_repos + synced_repos

        self.write_metadata(self.repos)
        return synced_repos

    def write_metadata(self, repos: List[Repository]):
        """
        Writes the metadata of cloned repositories to a JSON file.

        Args:
            repos (List[Repository]): A list of Repository dataclass objects.
        """
        metadata = [repo.__dict__ for repo in repos]
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Repository metadata written to {self.metadata_file}")

def fetch_repos_under_group(url: str) -> List[str]:
    """
    Fetches all repository URLs under a given GitLab or GitHub group URL.

    Args:
        url (str): The URL of the group (e.g., https://gitlab.com/my-group or https://github.com/my-org).

    Returns:
        List[str]: A list of repository URLs found under the group.
    """
    parsed_url = urllib.parse.urlparse(url)
    hostname = parsed_url.hostname
    path_parts = parsed_url.path.strip('/').split('/')

    repo_urls = []

    if "github.com" in hostname:
        if len(path_parts) < 1:
            print(f"Invalid GitHub group URL: {url}")
            return []
        org_name = path_parts[0]
        api_url = f"https://api.github.com/orgs/{org_name}/repos"
        page = 1
        while True:
            response = requests.get(api_url, params={'page': page, 'per_page': 100, 'sort': 'updated'})
            if response.status_code != 200:
                print(f"Error fetching GitHub repositories: {response.status_code}")
                break
            repos_data = response.json()
            if not repos_data:
                break
            for repo in repos_data:
                repo_urls.append(repo['clone_url'])
            page += 1

    elif "gitlab.com" in hostname:
        if len(path_parts) < 1:
            print(f"Invalid GitLab group URL: {url}")
            return []
        group_path = '/'.join(path_parts)
        api_url = f"https://gitlab.com/api/v4/groups/{urllib.parse.quote_plus(group_path)}/projects"
        page = 1
        while True:
            response = requests.get(api_url, params={'page': page, 'per_page': 100})
            if response.status_code != 200:
                print(f"Error fetching GitLab repositories: {response.status_code}")
                break
            repos_data = response.json()
            if not repos_data:
                break
            for repo in repos_data:
                repo_urls.append(repo['http_url_to_repo'])
            page += 1
    else:
        print(f"Unsupported hosting platform for URL: {url}")

    return repo_urls

def filter_repos_according_to_user(repo_urls: List[str]) -> List[str]:
    """Interactively asks user which repos to be included and filters the rest

    Args:
        repo_urls (List[str]): The list of repository URLs to filter.

    Returns:
        List[str]: The list of selected repository URLs.
    """
    if not repo_urls:
        print("No repositories found to filter.")
        return []

    title = 'Select repositories to include (Space to toggle, Enter to confirm):'
    options = repo_urls

    selected_options = pick(options, title, multiselect=True, min_selection_count=0)

    return [option for option, index in selected_options]


if __name__ == "__main__":
    repos = fetch_repos_under_group("https://github.com/facebook")
    if repos:
        filtered_repos = filter_repos_according_to_user(repos)
        print(f"Selected Repositories: {filtered_repos}", )
