from dataclasses import dataclass

@dataclass
class Repository:
    """
    Represents a cloned git repository.

    Attributes:
        url (str): The URL of the repository.
        group_name (str): The group or organization name.
        repo_name (str): The name of the repository.
        repo_path (str): The local path to the cloned repository.
    """
    url: str
    group_name: str
    repo_name: str
    repo_path: str
