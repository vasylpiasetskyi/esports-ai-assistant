---
name: testing
description: Best practices for testing Python applications
---

# Testing Skill

## Goal

Write reliable, maintainable and fast tests.

## Framework

- pytest

## Principles

- Test behavior, not implementation.
- Prefer integration tests for business workflows.
- Keep unit tests isolated.
- Every public service should have tests.

## Fixtures

- Prefer reusable fixtures.
- Avoid overly complex fixture hierarchies.

## Mocking

Mock only external systems:

- OpenAI
- Qdrant
- HTTP requests
- File system (when appropriate)

Do not mock internal business logic.

## Naming

Test names should clearly describe behavior.

Example:

test_index_document_successfully

instead of

test_index

## Anti-patterns

Avoid:

- sleep()
- random values
- shared mutable state
- testing private methods