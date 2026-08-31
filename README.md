# Library Lending Manager

A persistent, keyboard-driven terminal application for managing books,
members, current loans, and complete borrowing history.

## Run the application

The project uses [uv](https://docs.astral.sh/uv/) and Python 3.14 or newer.

```bash
uv sync
uv run cli-library-lending-manager
```

You can also use Python's module entry point:

```bash
uv run python -m cli_library_lending_manager
```

Use the arrow keys and Enter to navigate. Press `Q` to leave the current menu.

## Features

- Automatically generated stable book, member, and loan IDs.
- Validated add, update, search, browse, and removal workflows.
- Selectable records instead of requiring users to memorize IDs.
- Fourteen-day checkout period and return history preserved exactly once.
- Active, overdue, returned, and complete loan views.
- Available-book and on-loan views plus category and author sorting.
- Detailed book and member screens with current and historical relationships.
- Derived dashboard statistics, availability, and due-date cues.
- Pagination for long terminal lists.
- Automatic atomic JSON persistence after every successful mutation.
- Safe startup handling for missing, malformed, or structurally invalid data.
- Explicit timestamped JSON backup/export.

## Architecture

```text
presentation -> application -> domain
                         ^
                         |
                   persistence
```

- `domain` defines `Book`, `Member`, `Loan`, `LibraryState`, and shared stable-ID
  matching rules. It has no terminal or JSON knowledge.
- `application` contains the `Library` workflows and derived queries. It
  validates complete operations before mutating state.
- `persistence` converts canonical records to and from JSON. `JsonStorage`
  handles generic atomic file replacement; `JsonLibraryStore` understands the
  library schema and validates loaded relationships.
- `presentation` contains reusable arrow-key menus and `LibraryCLI`, which
  gathers input, calls application operations, and displays results.
- `bootstrap.py` loads the store and connects one `Library` instance to the UI.

## Data model and invariants

```text
Book:   ID, title, author, category
Member: ID, name
Loan:   ID, book ID, member ID, checkout date, due date, returned date
```

- IDs are displayed as `B001`, `M001`, and `L001` and generated automatically.
- Exact ID comparison trims outside whitespace and uses `str.casefold()`, so
  `B001`, `b001`, and `" B001 "` are equivalent.
- Generated IDs are not reused when historical loans still reference them.
- A book can have at most one active loan.
- Checkout requires an existing book and member.
- Due date is checkout date plus exactly 14 calendar days.
- A loan is active when `returned_date` is `None`.
- A loan can be returned once, never before checkout, and is retained forever.
- Books or members with active loans cannot be removed.
- Returned history may retain IDs of books or members removed later.

Availability, active/overdue status, and statistics are derived from canonical
records. They are not stored as competing flags or counters.

## Persistence and recovery

The default file is:

```text
data/library.json
```

The top-level JSON shape is:

```json
{
  "books": [],
  "members": [],
  "loans": []
}
```

Dates use ISO `YYYY-MM-DD` strings. Successful mutations are first written to a
temporary file and then replace the canonical file. If saving fails, the
in-memory mutation is rolled back.

A missing file starts an empty library. Malformed JSON, invalid fields,
duplicate IDs, impossible dates, broken active references, and multiple active
loans for one book are rejected. The bad file is left untouched. The user may
quit or start a temporary session in which saving and backup are disabled.

`Export backup` writes a timestamped copy under `data/backups/` without changing
the canonical file.

## Search and ordering

- Book text search is case-insensitive and partial across title, author, and
  category.
- Member text search is case-insensitive and partial across name.
- Default books: title, then author, then ID.
- Author view: author, then title, then ID.
- Members: name, then ID.
- Active loans: due date, then ID.
- Complete history: newest checkout first, then ID.
- A loan is overdue only while active and when `due_date < today`; a loan due
  today is not overdue.

## Presentation dependency

The only third-party runtime dependency is `readchar`. It is restricted to the
presentation layer and provides reliable cross-platform arrow-key input. All
domain, validation, relationship, date, and persistence logic belongs to this
project.

## Verification

Run the automated suite:

```bash
uv run python -m unittest discover -s tests -v
```

The suite covers domain records, ID normalization, CRUD validation, search,
ordering, checkout/return invariants, overdue boundaries, statistics,
pagination, details, atomic persistence, invalid data, rollback, backups,
startup recovery, and complete restart lifecycles.

Observed manual verification includes launching the real terminal UI,
navigating nested menus, adding generated-ID records, selecting records without
typing IDs, persisting across restarts, returning loans, viewing history, and
confirming blocked deletion during an active loan.

Additional design notes live in [`docs/`](docs/).
