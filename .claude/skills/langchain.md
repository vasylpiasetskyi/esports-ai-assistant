---
name: langchain
description: Best practices for building LangChain applications
---

# LangChain Skill

## Principles

- Use official LangChain abstractions.
- Prefer LCEL over legacy chains.
- Use Runnable interfaces.
- Avoid deprecated APIs.

## Preferred Components

- Document
- DocumentLoader
- RecursiveCharacterTextSplitter
- OpenAIEmbeddings
- Qdrant
- Retriever
- PromptTemplate

## Avoid

- Custom wrappers around LangChain unless necessary.
- Deprecated chains.
- Hidden magic.

## Project Goal

Expose LangChain concepts clearly.

Educational value is more important than minimizing code.