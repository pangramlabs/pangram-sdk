# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the official Python SDK for the Pangram Labs API, which provides AI-generated text detection and plagiarism checking services.

## Build and Development Commands

**Install dependencies:**
```bash
poetry install
```

**Run tests (requires PANGRAM_API_KEY environment variable):**
```bash
poetry run python -m unittest tests/pangram_test.py
```

**Run a single test:**
```bash
poetry run python -m unittest tests/pangram_test.py::TestPredict::test_predict
```

**Build documentation:**
```bash
poetry install --with docs
cd docs && make html
```

## Architecture

The SDK is minimal with two main files:

- `pangram/__init__.py` - Exports `Pangram` (alias for `PangramText`) as the main client class
- `pangram/text_classifier.py` - Contains the `PangramText` class with all API methods

### API Methods

- `predict(text)` - Main V3 endpoint for AI-assistance detection with segment-level analysis
- `check_plagiarism(text)` - Plagiarism detection against online content database

### API Configuration

API endpoints are defined as constants at the top of `text_classifier.py`. The SDK uses `requests` for HTTP calls and authenticates via `x-api-key` header.
