"""Small, strict helpers for extracting structured LLM output."""

from __future__ import annotations

import json
from typing import Any


def extract_json(text: str, expected_type: type) -> Any:
    """Extract the first balanced JSON object/array of ``expected_type``."""
    opener, closer = ("[", "]") if expected_type is list else ("{", "}")
    start = text.find(opener)
    if start < 0:
        raise ValueError("response does not contain JSON")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                value = json.loads(text[start : index + 1])
                if not isinstance(value, expected_type):
                    raise ValueError(f"expected {expected_type.__name__} JSON")
                return value
    raise ValueError("JSON payload is not balanced")
