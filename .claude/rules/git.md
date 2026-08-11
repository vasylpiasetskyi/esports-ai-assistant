---
name: git
description: Git workflow guidelines
---

# Git Rules

## Commits

One logical change per commit.

Avoid mixing refactoring with new functionality.

## Assistant Behavior

Claude must never run `git commit` on its own.

Before every commit, Claude must output a short, ready-to-use commit
message and let the user decide what happens next — either the user
tells Claude to commit with it, or the user copies it and commits
themselves. Claude must not run `git commit` unless the user explicitly
says so for that message. This applies even mid-plan or mid-task, and
even when a batch-commit workflow is otherwise in effect. Preparing/
staging changes is fine without asking; the commit itself always
requires explicit go-ahead first.

## Commit Messages

Use clear commit messages.

Examples:

Add Liquipedia crawler

Implement Qdrant indexer

Refactor retriever service

## Documentation

If architecture changes,
update documentation in the same commit.

## Refactoring

Do not perform large unrelated refactorings while implementing a feature.

## Pull Requests

Every pull request should have a single clear purpose.