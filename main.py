import asyncio
from typing import List
from repository_manager import RepoManager
from repository import Repository
from processing import process_repo, read_output
from token_utils import print_file_tokens

def sync_repositories()->List[Repository]:
    repository_list = [
        "https://github.com/paul-gauthier/aider.git",
        "https://github.com/tree-sitter/tree-sitter-python.git",
    ]
    repo_manager = RepoManager(repository_urls=repository_list)
    print("\nCloned Repositories:")
    for repo in repo_manager.repos:
        print(f"- {repo.group_name}/{repo.repo_name} at {repo.repo_path}")
    return repo_manager.repos


def main():
    repos = sync_repositories()
    asyncio.run(process_repo("Qwen/Qwen3-8B", repos[1], token_limit=24000))


if __name__ == "__main__":
    main()
