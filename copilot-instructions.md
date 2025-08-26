## Project Overview
- A Django reusable app that renders Django Admin list filters with an autocomplete widget.
- Targets Django 4.2–5.2 and Python 3.10+.
- Provides a factory for quickly creating autocomplete list filters and an auto-registered admin view endpoint for dropdown data.

## Folder Structure
- `admin_auto_filters/`
  - `apps.py`: AppConfig; auto-registers the admin autocomplete endpoint by patching `admin.site.get_urls()` during `ready()`.
  - `filters.py`: Core filter classes and `AutocompleteFilterFactory` used in `ModelAdmin.list_filter`.
  - `views.py`: Subclass of Django’s `AutocompleteJsonView`; uses Django 4.2+ contract (`process_request`, `serialize_result`).
  - `templates/`, `static/`: Assets for the admin widget.
  - `__init__.py`: Package metadata and constants:
    - `ADMIN_AUTOCOMPLETE_VIEW_SLUG = 'admin-autocomplete'`
    - `ADMIN_AUTOCOMPLETE_VIEW_NAME = f"admin:{ADMIN_AUTOCOMPLETE_VIEW_SLUG}"`
- `tests/`
  - `tests/tests/`: Minimal Django project (settings, urls, wsgi).
  - `tests/testapp/`: Test application (models, admin, migrations, fixtures, tests).
    - `migrations/`: App migrations including showcase models for docs/tests.

Libraries and Frameworks
------------------------
- Django (>= 4.2, < 6): admin, widgets, and autocomplete view.
- Typing: `typing`, `django-stubs`, `django-stubs-ext` for type checking.
- Tooling: Ruff (lint + format), MyPy (type checking), setuptools for packaging.

Coding Standards
----------------
- General
  - Use Python 3.10+ features (e.g., `|` for unions if needed, but prefer explicit types per project style).
  - Keep changes minimal, focused, and backward compatible. Avoid refactors/big whitespace changes outside the scope of the issue/PR.
  - Preserve public APIs and documented behavior.
  - Prefer single quotes for strings; f-strings for interpolation.
  - Keep imports sorted and grouped; let Ruff handle final ordering.
  - Do not add license headers to files.

- Django
  - Admin autocomplete endpoint:
    - Use the constants `ADMIN_AUTOCOMPLETE_VIEW_SLUG` and `ADMIN_AUTOCOMPLETE_VIEW_NAME` for routes and reversing.
    - Do not modify the project’s root `urls.py`; register routes by patching `admin.site.get_urls()` in `AppConfig.ready()` only.
    - Always wrap admin views with `admin_site.admin_view(...)` for permissions/CSRF.
  - The autocomplete view must follow Django 4.2+ contract:
    - Extract params via `process_request(request)` which validates `app_label`, `model_name`, `field_name`.
    - Implement/override `serialize_result(obj, to_field_name)`; return `{"id": str(...), "text": ...}`.
    - Query building should call `get_queryset()` → `model_admin.get_search_results()` and apply `source_field.get_limit_choices_to()`.
  - Filters created via `AutocompleteFilterFactory` default to the package’s endpoint: `ADMIN_AUTOCOMPLETE_VIEW_NAME`.
  - When adding examples/tests, ensure the remote model’s admin defines `search_fields`, per Django admin autocomplete requirements.

Linting Standards
-----------------
- Ruff (configured in `pyproject.toml`)
  - Run `ruff check --fix` and `ruff format` on changed files.
  - Keep import blocks organized; fix `I001` warnings.
  - Respect the existing `lint.select`/`lint.ignore` rules; do not churn unrelated files.

- MyPy
  - Strictness tuned via `pyproject.toml` and `mypy_django_plugin`.
  - Add or refine type annotations for new/changed code. Avoid `Any` when feasible.
  - Keep generics and return types explicit; prefer precise types in public APIs.

Typing Expectations
-------------------
- Type everything you add or significantly modify (functions, methods, attributes).
- Use `typing` and `collections.abc` types as appropriate.
- For trivial `__str__`/`__repr__`, annotate but keep implementations simple.

Testing
-------
- Run tests via:
  - `./tests_manage.py test tests`
- Write tests in `tests/testapp/tests.py` using Django’s `TestCase`.
- Prefer integration-style tests that hit:
  - Admin changelists using `list_filter` with `AutocompleteFilter`/`AutocompleteFilterFactory`.
  - The admin autocomplete endpoint (`reverse(ADMIN_AUTOCOMPLETE_VIEW_NAME)`) with required query params: `app_label`, `model_name`, `field_name`.
- When adding models for tests, create migrations in `tests/testapp/migrations/` and, if needed, seed minimal data inside tests or via fixtures.
- Keep tests deterministic; assert both inclusion and exclusion where helpful.

Documentation
-------------
- Update `README.md` with concise examples when adding notable features.
- Examples must be valid for Django 4.2+ and include `search_fields` on remote admins.
- Reference the public constants for endpoint names in docs/snippets.

PR & Commit Guidance
--------------------
- Use concise, descriptive commit messages with a scope prefix when helpful (e.g., `tests(...)`, `feat(...)`, `fix(...)`).
- Avoid mixing unrelated changes in one PR.
- Ensure tests and linters pass locally before opening the PR.
