import logging


def build_prompt(code_snippet, rule, file_path, line_number):
    """
    Builds a prompt to ask the AI to fix a code issue
    and return the response in JSON format.
    """
    logging.debug(f"Building prompt for {file_path}:{line_number}")

    rule_name = rule.get("name", "Unknown rule")
    rule_description = rule.get(
        "Description", rule.get("description", "No description available")
    )
    rule_language = rule.get("language", "unknown")
    rule_parameters = rule.get("parameters", {})

    logging.debug("Rule details:")
    logging.debug(f"   Name: {rule_name}")
    logging.debug(f"   Language: {rule_language}")
    logging.debug(f"   Description: {rule_description}")
    logging.debug(f"   Parameters: {rule_parameters}")

    parameters_text = ""
    if rule_parameters:
        parameters_text = f"\nRule parameters: {rule_parameters}"
        logging.debug("Rule parameters added to prompt")
    else:
        logging.debug("No rule parameters to add")

    json_example = (
        '{"original": "problematic original code line", '
        '"fixed": "corrected code line"}'
    )

    prompt = f"""You are a {rule_language} code expert. \
Analyze this issue and provide a fix.

**Identified Problem:**
- File: {file_path}
- Line: {line_number}
- Rule: {rule_name}
- Description: {rule_description}{parameters_text}

**Code in question:**
```{rule_language}
{code_snippet}
```

**Instructions:**
1. Identify the exact line that has the problem
2. Provide a correction that follows the rule
3. Return ONLY valid JSON - no markdown blocks, no explanations, no additional text
4. Use exactly this JSON structure:

{json_example}

IMPORTANT: Your response must be pure JSON only, with "original" and "fixed" \
fields containing the problematic code and its correction respectively. \
Do not wrap in markdown blocks."""

    logging.debug(f"Prompt built successfully ({len(prompt)} characters)")
    logging.debug(f"Full prompt content:\n{'-' * 50}\n{prompt}\n{'-' * 50}")

    return prompt
