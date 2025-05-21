from transformers import AutoTokenizer
from file_reader import read_source_files, read_codefile
from typing import Dict, Tuple, List, Optional
from repository import Repository

def get_file_tokens(model_name: str, repo_path: str, token_limit: Optional[int] = None) -> Dict[str, int]:
    """
    Reads source files from a repository, tokenizes their content using a specified model,
    and returns a dictionary mapping file paths to their token counts.

    Args:
        model_name (str): The name of the pre-trained tokenizer model to use.
        repo_path (str): The path to the code repository.
        token_limit (Optional[int]): The maximum number of tokens allowed per file. Files
                                     exceeding this limit or having zero tokens will be excluded.

    Returns:
        Dict[str, int]: A dictionary where keys are file paths and values are token counts
                        for files within the specified token limit and with non-zero tokens.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    file_tokens: Dict[str, int] = {}
    for sourcefilename in read_source_files(repo_path).source_files:
        code = read_codefile(sourcefilename)
        num_tokens = len(tokenizer.encode(code))
        if num_tokens == 0:
            print(f"Skipping file {sourcefilename} as it has zero tokens.")
            continue
        if token_limit is not None and num_tokens > token_limit:
            print(f"Skipping file {sourcefilename} with {num_tokens} tokens, exceeding the limit of {token_limit}.")
            continue
        file_tokens[sourcefilename] = num_tokens
    return file_tokens

def print_file_tokens(model_name: str, repo: Repository, token_limit: Optional[int] = None):
    """
    Prints file paths and their token counts, sorted by token count in descending order,
    and also prints the total token count.

    Args:
        model_name (str): The name of the pre-trained tokenizer model to use.
        repo (Repository): The Repository object representing the code repository.
        token_limit (Optional[int]): The maximum number of tokens allowed per file for filtering.
    """
    file_tokens = get_file_tokens(model_name, repo.repo_path, token_limit)
    source_files_with_tokens: List[Tuple[str, int]] = list(file_tokens.items())

    total_tokens = sum(file_tokens.values())

    # Sort in descending order of num_tokens
    source_files_with_tokens.sort(key=lambda item: item[1], reverse=True)

    print(f"\nToken counts for repository: {repo.group_name}/{repo.repo_name}")
    for sourcefilename, num_tokens in source_files_with_tokens:
        print(sourcefilename, f"{num_tokens} tokens")

    print(f"\nTotal tokens: {total_tokens}")
