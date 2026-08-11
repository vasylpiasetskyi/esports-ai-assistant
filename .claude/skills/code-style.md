---
name: code-style
description: General Python coding style and readability guidelines
---

# Code Style Skill

## Goal

Produce clean, readable and maintainable code.

## Readability

- Explicit is better than implicit.
- Readability is more important than cleverness.
- Prefer simple solutions.

## File Size

Target:

- Files under 300 lines.
- Functions under 40 lines.
- Classes under 200 lines.

These are guidelines, not strict limits.

## Naming

Use descriptive names.

Good:

DocumentIndexer

RetrieverService

EmbeddingProvider

Avoid:

Utils

Common

Manager

Helper

Processor

## Imports

- Standard library
- Third-party
- Local imports

Avoid wildcard imports.

## Comments

Comment why.

Avoid commenting what the code already explains.

## Functions

Each function should have one responsibility.

Prefer early returns.

Avoid deeply nested code.

## Classes

Keep classes focused.

If a class has multiple unrelated responsibilities,
split it.

## Logging

Use structured logging.

Never print() in production code.