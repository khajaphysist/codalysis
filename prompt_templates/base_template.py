def base_template(code: str, json_schema: str, task: str)->str:
    return f"""You are an expert code analyst. Your task is to analyze the provided code snippet and provide the information requested in a structured JSON format provided at the end.

**Code**

```
{code}
```

**Task or Information Required**
{task}

**Required JSON format**

```json
{json_schema}
```

Always output a valid JSON object and Do not include any text or explanation outside the JSON structure /no_think
"""
