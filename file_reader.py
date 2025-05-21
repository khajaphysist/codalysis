import os
from typing import List
from constants import GENERAL_FILE_EXTENSIONS, SOURCE_FILE_EXTENSIONS, FULL_FILES, IGNORE_FILE_EXTENSIONS
from pydantic import BaseModel

class SourceFiles(BaseModel):
    general_files: List[str]
    source_files: List[str]
    full_files: List[str]


def read_codefile(filename: str)->str:
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def read_source_files(src_dir: str) -> SourceFiles:
    general_files = []
    source_files = []
    full_files = []
    for root, _, files in os.walk(src_dir):
        if any(part.lower() in ["test", "tests", "spec", "specs"] for part in root.split(os.sep)):
            print(f"Skipping directory {root} as it appears to be a test directory.")
            continue
        for file in files:
            file_path = os.path.join(root, file)
            file_name = os.path.basename(file_path)
            # for extensions like .min.js
            if any(file_path.endswith(ext) for ext in IGNORE_FILE_EXTENSIONS):
                print(f"Skipping file {file_path} due to ignored extension.")
                continue
            file_extension = os.path.splitext(file_path)[1]
            if file_extension in GENERAL_FILE_EXTENSIONS:
                general_files.append(file_path)
            elif file_extension in SOURCE_FILE_EXTENSIONS:
                source_files.append(file_path)
            elif file_name in FULL_FILES:
                full_files.append(file_path)
    return SourceFiles(general_files=general_files, source_files=source_files, full_files=full_files)
