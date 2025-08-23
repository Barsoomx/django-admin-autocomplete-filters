Changelog
=========

All notable changes to this project will be documented in this file.
This project adheres to Keep a Changelog and semantic versioning.

0.6.0rc2 — 2025-08-23
---------------------

Added
- Publish workflow now publishes both pre-releases and finals to PyPI, with metadata inspection.
- Pre-commit configuration (Ruff + Mypy) and contributor docs.

Changed
- Use SPDX license expression and modern license-files config.
- Clean build artifacts in publish workflow before building.

0.6.0rc1 — 2025-08-23
---------------------

Added
- PEP 621 packaging via `pyproject.toml` (setuptools backend).
- GitHub Actions test matrix for Python 3.10–3.12 and Django 4.2, 5.0, 5.1, 5.2.
- PyPI publish workflow using Trusted Publishing (OIDC) on GitHub Releases.
- Ruff configuration and GitHub Actions lint job.
- Documentation updates noting this is a maintained continuation of the original project.

Changed
- Project name for distribution: `django-admin-autocomplete-filters`.
- Fixed Django 5 compatibility by importing `lookup_spawns_duplicates` from `django.contrib.admin.utils`.

Removed
- `setup.py` and `requirements.txt` in favor of `pyproject.toml` only builds.

Notes
- Python import path remains `admin_auto_filters` for backward compatibility.
