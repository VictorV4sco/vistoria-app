# VistoriaApp — Instructions for Codex

## Project context

VistoriaApp is a local Windows desktop application for creating and
standardizing real-estate inspection reports.

Before implementing features, read:

- docs/especificacao-mvp-v1.md
- docs/backlog-implementacao-mvp-v1.md

These documents are the source of truth for the MVP.

Do not add features outside the documented MVP unless explicitly requested.

---

## Development methodology

This project uses strict TDD for business logic.

For every new business behavior:

1. Write or update the test first.
2. Run the relevant test.
3. Confirm that it fails for the expected reason.
4. Implement the minimum necessary code.
5. Run the relevant test again.
6. Refactor if useful.
7. Run the complete test suite.
8. Run lint.

Do not implement business behavior before a corresponding failing test exists.

---

## Testing

Run the full test suite with:

```bash
docker compose run --rm test
