#!/usr/bin/env python3
"""
Simple JSON parsing utility for handling Claude API responses
"""

import json
import re


def safe_json_parse(response_text):
    """
    Safely parse JSON from Claude API response, handling various formats
    """
    # Clean up the response text
    response_text = response_text.strip()

    # Try to extract JSON from markdown code blocks
    if "```json" in response_text:
        # Find the first occurrence of ```json
        start_marker = "```json"
        start_pos = response_text.find(start_marker)

        if start_pos != -1:
            # Find the first occurrence of ``` after the start marker
            end_marker = "```"
            # Look for the first ``` that comes after our content start
            content_start = start_pos + len(start_marker)

            # Find the first ``` that comes after content_start
            end_pos = -1
            # More robust search for end marker - scan more carefully
            for i in range(content_start, len(response_text) - 2):
                if response_text[i : i + 3] == end_marker:
                    end_pos = i
                    break

            if end_pos != -1:
                # Extract content between markers, excluding the markers themselves
                extracted = response_text[content_start:end_pos]
                # Clean up any leading/trailing whitespace and newlines
                extracted = extracted.strip()
                response_text = extracted

    # Try to fix common escaped quote issues that cause parsing problems
    # The main issue appears to be with \" inside string values where it's not properly escaped
    try:
        return json.loads(response_text)
    except:
        pass

    # Try to fix common escaped quote issues that cause parsing problems
    try:
        # Replace malformed escaped quotes - this fixes the specific case mentioned
        # where there are \" that should be just "
        fixed_text = response_text.replace('\\""', '"')  # Replace \" with "
        fixed_text = fixed_text.replace('\\\\\\"', '\\"')  # Fix double escapes
        fixed_text = fixed_text.replace('\\\\"', '"')  # Fix other escape issues
        return json.loads(fixed_text)
    except:
        pass

    # If that still fails, try to find and extract JSON array more carefully
    try:
        # Find the first JSON array (start with [ and end with ])
        # This looks for a balanced bracket pattern to handle complex nested structures
        bracket_count = 0
        start_pos = -1
        end_pos = -1

        for i, char in enumerate(response_text):
            if char == "[":
                if start_pos == -1:
                    start_pos = i
                bracket_count += 1
            elif char == "]":
                bracket_count -= 1
                if bracket_count == 0 and start_pos != -1:
                    end_pos = i
                    break

        if start_pos != -1 and end_pos != -1:
            array_content = response_text[start_pos : end_pos + 1]
            return json.loads(array_content)
    except:
        pass

    # Try to find and extract valid JSON objects/arrays with more robust methods
    try:
        # Look for content between braces or brackets to extract first valid structure
        # This handles cases where there might be extraneous text at the start or end
        for i in range(len(response_text)):
            if response_text[i] in "[{":
                # Found a potential start
                char = response_text[i]
                bracket_pairs = {"[": "]", "{": "}"}
                stack = [i]
                depth = 1

                # Find matching end bracket
                j = i + 1
                while j < len(response_text) and depth > 0:
                    if response_text[j] == char:
                        depth += 1
                        stack.append(j)
                    elif response_text[j] == bracket_pairs[char]:
                        depth -= 1
                        stack.pop()
                    j += 1

                if depth == 0 and len(stack) > 0:
                    # Extract the JSON structure
                    json_content = response_text[i:j]
                    return json.loads(json_content)
    except:
        pass

    # Try to find any JSON object or array with basic validation
    try:
        # Try to find JSON-like structure with quotes and braces/brackets
        # First try to find the first bracket or brace and parse from there
        bracket_positions = []
        brace_positions = []

        for i, char in enumerate(response_text):
            if char == "[":
                bracket_positions.append(i)
            elif char == "{":
                brace_positions.append(i)

        # Try to extract from the earliest bracket or brace
        positions = sorted(bracket_positions + brace_positions)
        for pos in positions:
            # Try to parse forward from this position to find balanced structure
            try:
                # Find the matching closing bracket/brace
                char = response_text[pos]
                if char == "[":
                    end_char = "]"
                else:  # '{'
                    end_char = "}"

                stack = [pos]
                i = pos + 1
                while i < len(response_text) and len(stack) > 0:
                    if response_text[i] == char:
                        stack.append(i)
                    elif response_text[i] == end_char:
                        stack.pop()
                    i += 1

                if len(stack) == 0 and i > pos + 1:
                    json_content = response_text[pos:i]
                    return json.loads(json_content)
            except:
                continue
    except:
        pass

    # If everything fails, return None
    return None


# Test the function
if __name__ == "__main__":
    # Test cases
    test_cases = [
        '{"test": "value"}',
        '```json\n{"test": "value"}\n```',
        'Some text\n```json\n{"test": "value"}\n```\nMore text',
        '{"test": "value with \\"quotes\\""}',
    ]

    for i, test in enumerate(test_cases):
        result = safe_json_parse(test)
        print(f"Test {i + 1}: {result}")
