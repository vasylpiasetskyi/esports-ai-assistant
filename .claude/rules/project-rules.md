---
name: project-rules
alwaysApply: true
---

# Project Rules

These rules apply to the entire repository.

## Architecture

Never violate the project architecture.

Do not mix responsibilities between layers.

## Learning First

This repository is a learning project.

Prefer implementations that clearly demonstrate LangChain concepts.

Avoid hiding important concepts behind unnecessary abstractions.

## Quality

Write production-quality code.

Do not generate placeholder implementations unless explicitly requested.

## Documentation

Whenever architecture changes:

- update TDD
- update architecture documentation
- update ADRs when appropriate

## Consistency

Follow existing project conventions.

Do not introduce multiple styles for solving the same problem.