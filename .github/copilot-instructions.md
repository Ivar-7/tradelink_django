# Development Guidelines (TukiStudy Backend)

These rules guide all code changes to keep the project robust and consistent.

- Production quality: Write secure, performant, and maintainable code. Handle errors explicitly and validate inputs.
- Modularity: Separate concerns. Keep business logic in dedicated service layers (e.g., `app_name/services/`), keep views thin, avoid fat models.
- App deliverables: For every Django app, include:
  - `README.md`: **MINIMAL** - quickstart, seed command, test command and important information. Swagger has all endpoint docs.
  - `postman_collection.json`: up-to-date API requests for that app.
  - Seed data: `management/commands/seed_<app>.py` to create demo data (idempotent).
- API design: Use DRF ViewSets + routers, proper permissions, and serializers. Version APIs under `/api/v1/`.
- Swagger: ALWAYS add comprehensive drf-spectacular annotations (`@extend_schema`, `@extend_schema_view`) to all ViewSets. Swagger (`/api/docs/`) is the primary API documentation.
- Swagger: Document all ViewSets with drf-spectacular (`@extend_schema`, `@extend_schema_view`); `/api/docs/` is canonical.
- Schemas: Put drf-spectacular decorators and OpenAPI defs in an app-level `schemas.py` and import the composed decorator into `views.py`.
- User vs Admin endpoints: For resources where both regular users and admins interact, **use separate ViewSets**:
  - `/resource/` – user-only ViewSet (queryset filtered to `user=request.user`)
  - `/admin/resource/` – admin-only ViewSet with filters for user, status, etc.
  - This keeps auditing clear, Swagger docs accurate, and avoids role-based conditional logic in one ViewSet.
- Auth: Use JWT (SimpleJWT). Avoid leaking sensitive info in responses.
- Config: Use environment variables for secrets and external URLs. Create a `.env.example` listing required variables.
- Observability: Add logging at boundaries (requests, services) and avoid noisy logs.
- Tests: Prefer unit tests for services and API tests for endpoints.
- Environment: Activate the virtualenv before running Django commands (`venv\Scripts\Activate.ps1` on Windows, `source venv/bin/activate` on Unix).
- Always run check after code changes:
  ```bash
  python manage.py check
  ```
  No issues should be present.

When in doubt, prefer clarity and separation over cleverness.