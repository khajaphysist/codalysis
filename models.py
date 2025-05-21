from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from prompt_templates.file_level import FunctionDescription as BaseFunctionDescription, FileDescription as BaseFileDescription

class ExtendedFunctionDescription(BaseFunctionDescription):
    """
    Extends the base FunctionDescription with repository and file information.
    """
    filepath: str
    repository_url: str
    group_name: str
    repo_name: str
    
    def to_vector_string(self) -> str:
        """
        Generates a paragraph-style string representation of the function description,
        suitable for feeding into a vector database.
        """
        description_parts = []

        if self.class_name:
            description_parts.append(
                f"Within the file '{self.filepath}', the method '{self.function_name}' belonging to the class '{self.class_name}' serves the following purpose:"
            )
        else:
            description_parts.append(
                f"The function '{self.function_name}' located in the file '{self.filepath}' is designed to:"
            )

        description_parts.append(f"{self.functionality}")

        if self.arguments:
            arg_descriptions = []
            for arg in self.arguments:
                arg_descriptions.append(arg.to_paragraph_string())
            description_parts.append("It accepts the following arguments: " + " ".join(arg_descriptions))
        else:
            description_parts.append("It accepts no arguments.")

        description_parts.append(f"The function returns a value of type '{self.return_type}'.")

        if self.tags:
            tags_string = ", ".join(self.tags)
            description_parts.append(f"This function can be categorized by the following tags: {tags_string}.")

        return " ".join(description_parts)

class ExtendedFileDescription(BaseFileDescription):
    """
    Extends the base FileDescription with repository and file information.
    """
    filepath: str
    repository_url: str
    group_name: str
    repo_name: str
    
    def to_vector_string(self) -> str:
        """
        Generates a paragraph-style string representation of the file description,
        suitable for feeding into a vector database.
        """
        description_parts = []

        description_parts.append(f"The file '{self.filepath}' serves the purpose:")
        description_parts.append(f"{self.overall_purpose_and_domain}")

        formatted_responsibilities = []
        for i, resp in enumerate(self.primary_responsibilities):
            # Remove trailing periods if any, to avoid double punctuation when joining
            cleaned_resp = resp.rstrip('.')
            if i == 0:
                formatted_responsibilities.append(cleaned_resp)
            else:
                # Lowercase the first letter for subsequent responsibilities to make it flow
                formatted_responsibilities.append(cleaned_resp[0].lower() + cleaned_resp[1:])

        if len(formatted_responsibilities) == 1:
            responsibilities_string = formatted_responsibilities[0]
            description_parts.append(f"Its primary responsibility is to {responsibilities_string.lower() if not responsibilities_string.split(' ')[0].istitle() else responsibilities_string}.")
        elif len(formatted_responsibilities) > 1:
            # Join all but the last with commas, and the last with 'and'
            responsibilities_joined = ", ".join(formatted_responsibilities[:-1]) + ", and " + formatted_responsibilities[-1]
            description_parts.append(f"Its primary responsibilities include: {responsibilities_joined}.")

        if self.tags:
            tags_string = ", ".join(self.tags)
            description_parts.append(f"This file is associated with the following keywords or tags: {tags_string}.")

        return " ".join(description_parts)

class AnalysisResults(BaseModel):
    """
    Represents the analysis results containing file and function descriptions.
    """
    file_descriptions: List[ExtendedFileDescription] = []
    function_descriptions: List[ExtendedFunctionDescription] = []
