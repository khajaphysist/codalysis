from .base_template import base_template
from pydantic import BaseModel, Field
from typing import List, Optional

class FileDescription(BaseModel):
    file_name: str = Field(default="", description="name of the file")
    overall_purpose_and_domain: str = Field(description="In under 1-2 clear and concise sentences, explain the file's primary purpose and the specific problem domain or area it belongs to. Example: 'This file implements a command-line interface (CLI) tool for parsing Apache log files and generating daily traffic reports.' or 'Defines utility functions for common string manipulation tasks, such as cleaning and normalizing text data for an NLP pipeline.'")
    primary_responsibilities: List[str] = Field(description="Each string in the list MUST describe a distinct, high-level responsibility of this file, starting with an action verb. Example: ['Parses user arguments from the command line.', 'Connects to the customer database.', 'Executes SQL queries to retrieve order information.', 'Formats query results into a JSON response.']")
    tags: List[str] = Field(description="Based on the detailed code analysis and its inferred purpose, suggest 5-7 specific and descriptive keywords or tags that categorize this file's responsibility (e.g., ['data-cleaning', 'text-normalization', 'user-input-validation', 'database-query', 'error-handling']). Output as a List[String].")

class Argument(BaseModel):
    name: str = Field(description="REQUIRED. String. name of the argument")
    type: str = Field(description="REQUIRED. String. type of the argument (be specific, e.g., List[int], Dict[str, Any])")
    usage: str = Field(description="REQUIRED. String. Detailed explanation of how the argument is used, its role, impact, and if it's optional or has defaults.")

    def to_paragraph_string(self) -> str:
        return f"The argument '{self.name}' is of type '{self.type}'. {self.usage}"

class FunctionDescription(BaseModel):
    file_name: str = Field(default="", description="name of the file")
    function_name: str = Field(description="REQUIRED. String. name of the function/method")
    class_name: Optional[str] = Field(default="", description="Optional. String. the class this method belongs to or empty otherwise")
    arguments: List[Argument]
    return_type: str = Field(description="REQUIRED. String. type of the return (be specific, e.g., str, None, Tuple[int, str])")
    functionality: str = Field(description="REQUIRED. String. A detailed, step-by-step summary of the function's purpose, logic, key operations, and any side effects. Be specific.")
    tags: List[str] = Field(description="REQUIRED. List of strings. Based on the detailed code analysis and its inferred purpose, suggest 5-7 specific and descriptive keywords or tags that categorize this function's functionality (e.g., ['data-cleaning', 'text-normalization', 'user-input-validation', 'database-query', 'error-handling']). Output as a List[String].")



def get_function_description_prompt(code: str)->str:
    return base_template(
        task="You are tasked with analyzing the provided code snippet and extracting detailed information about its functions and methods. For every function and method identified, including standalone functions and methods within classes, please provide a comprehensive description by populating the following JSON structure",
        code=code,
        json_schema="""
[
  {
    "function_name": "REQUIRED. String. name of the function/method",
    "class_name": "Optional. String. the class this method belongs to or empty otherwise",
    "arguments": [
      {
        "name": "REQUIRED. String. name of the argument",
        "type": "REQUIRED. String. type of the argument (be specific, e.g., List[int], Dict[str, Any])",
        "usage": "REQUIRED. String. Detailed explanation of how the argument is used, its role, impact, and if it's optional or has defaults."
      }
    ],
    "return_type": "REQUIRED. String. type of the return (be specific, e.g., str, None, Tuple[int, str])",
    "functionality": "REQUIRED. String. A detailed, step-by-step summary of the function's purpose, logic, key operations, and any side effects. Be specific.",
    "tags": [
      "REQUIRED. List of strings. Based on the detailed code analysis and its inferred purpose, suggest 5-7 specific and descriptive keywords or tags that categorize this function's functionality (e.g., ['data-cleaning', 'text-normalization', 'user-input-validation', 'database-query', 'error-handling']). Output as a List[String]."
    ]
  },
  ...
]
""",
    )

def get_file_description_prompt(code: str)->str:
    return base_template(
        task="You are an expert code analyst LLM. Your task is to provide a comprehensive file-level summary for the provided source code file. Analyze the entire file to understand its overall purpose, structure, dependencies, and key components. Populate the specified JSON output format with detailed and accurate information. This summary should provide a high-level overview, distinct from the granular function-by-function analysis",
        code=code,
        json_schema="""
{
  "overall_purpose_and_domain": "REQUIRED. String. In under 1-2 clear and concise sentences, explain the file's primary purpose and the specific problem domain or area it belongs to. Example: 'This file implements a command-line interface (CLI) tool for parsing Apache log files and generating daily traffic reports.' or 'Defines utility functions for common string manipulation tasks, such as cleaning and normalizing text data for an NLP pipeline.'",
  "primary_responsibilities": [
    "REQUIRED. List of strings. Each string in the list MUST describe a distinct, high-level responsibility of this file, starting with an action verb. Example: ['Parses user arguments from the command line.', 'Connects to the customer database.', 'Executes SQL queries to retrieve order information.', 'Formats query results into a JSON response.']"
  ],
  "tags": [
    "REQUIRED. List of strings. Based on the detailed code analysis and its inferred purpose, suggest 5-7 specific and descriptive keywords or tags that categorize this file's responsibility (e.g., ['data-cleaning', 'text-normalization', 'user-input-validation', 'database-query', 'error-handling']). Output as a List[String]."
  ]
}
"""
    )
