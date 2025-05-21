import os
import json
import asyncio
from typing import Optional, List
from model import get_response
from models import ExtendedFunctionDescription, ExtendedFileDescription, AnalysisResults
from prompt_templates.file_level import get_function_description_prompt, get_file_description_prompt
from file_reader import read_codefile
from repository import Repository
from token_utils import get_file_tokens
from pydantic import BaseModel


async def process_function_description(repo: Repository, filepath: str, code: str, output_filepath_base: str):
    """
    Processes a single file to generate and save function descriptions.
    """
    function_prompt = get_function_description_prompt(code)
    try:
        function_result = await get_response(prompt=function_prompt)

        validated_results = []
        for r in function_result:
            try:
                validated_r = ExtendedFunctionDescription(
                    file_name=os.path.basename(filepath),
                    filepath=os.path.relpath(filepath, repo.repo_path),
                    repository_url=repo.url,
                    group_name=repo.group_name,
                    repo_name=repo.repo_name,
                    **r
                )
                validated_results.append(validated_r.model_dump())
            except Exception as e:
                print(f"Error validating function description for file {filepath} with result: {json.dumps(r, indent=2)}. Error: {e}")


        with open(f"{output_filepath_base}.function.json", "w") as f:
            json.dump(validated_results, f, indent=2)

        print(f"Function analysis result for {filepath} saved to {output_filepath_base}.function.json")
    except Exception as e:
        print(f"Error processing function description for file {filepath}: {e}")

async def process_file_description(repo: Repository, filepath: str, code: str, output_filepath_base: str):
    """
    Processes a single file to generate and save a file description.
    """
    file_prompt = get_file_description_prompt(code)
    try:
        file_result = await get_response(prompt=file_prompt)

        try:
            validated_result = ExtendedFileDescription(
                file_name=os.path.basename(filepath),
                filepath=os.path.relpath(filepath, repo.repo_path),
                repository_url=repo.url,
                group_name=repo.group_name,
                repo_name=repo.repo_name,
                **file_result
            )
            validated_result_dict = validated_result.model_dump()
        except Exception as e:
            print(f"Error validating file description for file {filepath} with result: {json.dumps(file_result, indent=2)}. Error: {e}")

        with open(f"{output_filepath_base}.file.json", "w") as f:
            json.dump(validated_result_dict, f, indent=2)

        print(f"File analysis result for {filepath} saved to {output_filepath_base}.file.json")
    except Exception as e:
        print(f"Error processing file description for file {filepath}: {e}")

async def process_file(repo: Repository, filepath: str, code: str, base_output_dir: str, semaphore: asyncio.Semaphore):
    """
    Processes a single file by generating prompts for function and file descriptions,
    running the agent for both, and saving the results to separate JSON files.
    Uses a semaphore to limit concurrent access.
    """
    async with semaphore:
        print(f"Processing file: {filepath}")
        repo_output_dir = os.path.join(base_output_dir, repo.group_name, repo.repo_name)
        output_filepath_base = os.path.join(repo_output_dir, os.path.relpath(filepath, repo.repo_path))
        os.makedirs(os.path.dirname(output_filepath_base), exist_ok=True)

        await process_function_description(repo, filepath, code, output_filepath_base)
        await process_file_description(repo, filepath, code, output_filepath_base)


async def process_repo(model_name: str, repo: Repository, token_limit: Optional[int] = None, output_dir: str = "./output", concurrency: int = 50, max_files: Optional[int] = None):
    """
    Processes each source file in a repository in parallel by reading its content, generating prompts,
    and running the code analysis agent for both function and file descriptions. The results are
    saved as JSON files in the output directory with specific extensions.

    Args:
        model_name (str): The name of the pre-trained tokenizer model and the model for the agent.
        repo (Repository): The Repository object representing the code repository.
        token_limit (Optional[int]): The maximum number of tokens allowed per file for filtering.
        output_dir (str): The base directory where the analysis results will be saved.
        concurrency (int): The maximum number of files to process concurrently.
        max_files (Optional[int]): The maximum number of files to process in the repository.
    """
    file_tokens = get_file_tokens(model_name, repo.repo_path, token_limit)

    semaphore = asyncio.Semaphore(concurrency)
    tasks = []
    processed_files_count = 0
    total_tokens = 0
    for filepath in list((file_tokens.keys())):
        if max_files is not None and processed_files_count >= max_files:
            print(f"Reached maximum number of files to process ({max_files}). Skipping remaining files.")
            break

        code = read_codefile(filepath)
        num_tokens = file_tokens.get(filepath)
        total_tokens += num_tokens
        print(f"File: {filepath} has {num_tokens} tokens")
        tasks.append(process_file(repo, filepath, code, output_dir, semaphore))
        processed_files_count += 1

    print(f"Total input tokens: {total_tokens}")
    await asyncio.gather(*tasks)

def read_output(output_dir: str = "./output") -> AnalysisResults:
    """
    Reads all JSON files under the specified output directory and returns their content as an
    AnalysisResults object containing lists for file and function descriptions.
    """
    analysis_results = AnalysisResults()
    for root, _, files in os.walk(output_dir):
        for file in files:
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if file.endswith(".file.json"):
                        analysis_results.file_descriptions.append(ExtendedFileDescription.model_validate(data))
                    elif file.endswith(".function.json"):
                        analysis_results.function_descriptions.extend([ExtendedFunctionDescription.model_validate(d) for d in data])
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from file {filepath}: {e}")
            except Exception as e:
                print(f"Error reading file {filepath}: {e}")
    return analysis_results
