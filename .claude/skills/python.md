---
name: python
description: Python coding standards
---

# Python Skill

## Version

Python 3.13

## Rules

- Full typing.
- Pydantic v2.
- Google docstrings.
- dataclass when appropriate.
- pathlib instead of os.path.
- Use enums instead of string constants.

## Formatting

- Ruff
- Black

## File Organization

- Prefer files under 300 lines.
- Functions under 40 lines when practical.
- Classes should have a single responsibility.

## Error Handling

Raise meaningful exceptions.

Never silently ignore errors.